from state import PipelineState
from db import get_session
from models import PipelineLog
import os
from langchain_postgres import PGVector
from langchain_huggingface import HuggingFaceEmbeddings
from datetime import datetime
from langchain_groq import ChatGroq

# Maps keywords in the error message to a category name
# (matches your runbook filenames so retrieval lines up later)
ERROR_KEYWORDS = {
    "connection timeout": "connection_timeout",
    "schema mismatch": "schema_mismatch",
    "out of memory": "out_of_memory",
    "permission denied": "permission_denied",
    "upstream dependency": "upstream_dependency",
}

def log_analyzer_node(state: PipelineState) -> PipelineState:
    """
    Reads the most recent FAILED job from Postgres and classifies its error type.
    """
    session = get_session()
    latest_failure = (
        session.query(PipelineLog)
        .filter(PipelineLog.status == "FAILED")
        .order_by(PipelineLog.timestamp.desc())
        .first()
    )
    session.close()

    if not latest_failure:
        state["next_step"] = "no_failures"
        return state

    state["job_id"] = latest_failure.id
    state["job_name"] = latest_failure.job_name
    state["status"] = latest_failure.status
    state["error_message"] = latest_failure.message

    # Classify based on keyword matching
    category = "unknown"
    message_lower = latest_failure.message.lower()
    for keyword, cat in ERROR_KEYWORDS.items():
        if keyword in message_lower:
            category = cat
            break

    state["error_category"] = category
    state["analysis_confidence"] = "high" if category != "unknown" else "low"
    state["next_step"] = "retrieve_runbook"

    print(f"[Log Analyzer] Job '{state['job_name']}' failed with category: {category}")
    return state

PG_USER = os.getenv("POSTGRES_USER")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD")
PG_DB = os.getenv("POSTGRES_DB")
PG_CONNECTION = f"postgresql+psycopg://{PG_USER}:{PG_PASSWORD}@postgres:5432/{PG_DB}"

_embeddings = None
_vectorstore = None

def _get_vectorstore():
    """Lazily initializes the embedding model + vectorstore once, reuse afterwards."""
    global _embeddings, _vectorstore
    if _vectorstore is None:
        _embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
        )
        _vectorstore = PGVector(
            embeddings=_embeddings,
            collection_name="runbooks",
            connection=PG_CONNECTION,
            use_jsonb=True,
        )
    return _vectorstore

def doc_retriever_node(state: PipelineState) -> PipelineState:
    """
    Searches the runbook vectorstore using the error message,
    and attaches the most relevant runbook content to the state.
    """
    vectorstore = _get_vectorstore()

    query = state.get("error_message", "")
    results = vectorstore.similarity_search(query, k=1)

    if results:
        state["runbook_content"] = results[0].page_content
        state["retrieval_found"] = True
        state["next_step"] = "remediate"
        print(f"[Doc Retriever] Found matching runbook for category: {state.get('error_category')}")
    else:
        state["runbook_content"] = None
        state["retrieval_found"] = False
        state["next_step"] = "escalate"
        print(f"[Doc Retriever] No matching runbook found for category: {query}")

    return state

REMEDIATION_ACTIONS = {
    "connection_timeout": "retry",
    "schema_mismatch": "escalate",
    "out_of_memory": "retry_reduced_batch",
    "permission_denied": "escalate",
    "upstream_dependency": "retry_with_delay",
}

MAX_RETRIES = 2

def remediation_node(state: PipelineState) -> PipelineState:
    """Decides and executes a remediation action based on the error category.
    Logs the decision back to Postgres for auditability.
    """
    category = state.get("error_category", "unknown")
    retry_count = state.get("retry_count") or 0

    action = REMEDIATION_ACTIONS.get(category, "escalate")

    if action.startswith("retry") and retry_count >= MAX_RETRIES:
        action = "escalate"
        reason = f"Max retries ({MAX_RETRIES}) reached, escalating instead"
    else:
        reason = f"Action '{action}' taken for category '{category}'"

    state["recommended_action"] = action
    state["action_taken"] = reason
    state["retry_count"] = retry_count + 1 if action.startswith("retry") else retry_count

    print(f"[Remediation] Job '{state.get('job_name')}' -> Action: {action} ({reason})")

    session = get_session()
    log_entry = PipelineLog(
        job_name = state.get("job_name", "unknown"),
        status = "REMEDIATION",
        message = f"Action: {action}, Reason: {reason}, Original Error: {state.get('error_message')}",
        timestamp = datetime.utcnow(),
    )

    session.add(log_entry)
    session.commit()
    session.close()

    state["next_step"] = "done"
    return state

_llm = None
def _get_llm():
    """
    Lazily intializes the Groq LLM client, reuse afterwards.
    """
    global _llm
    if _llm is None:
        _llm = ChatGroq(
            model = "openai/gpt-oss-20b",
            temperature = 0.2,
            api_key = os.getenv("GROQ_API_KEY"),
        )
    return _llm

def summarize_incident_node(state: PipelineState) -> PipelineState:
    """
    Uses the Groq LLM to summarize the incident and the actions taken.
    """
    llm = _get_llm()
    prompt = f"""You are an SRE assistant summarizing a pipeline incident for a dashboard.
    Job: {state.get('job_name')}
    Error: {state.get('error_message')}
    Error category: {state.get('error_category')}
    Action taken: {state.get('action_taken')}
    Retry count: {state.get('retry_count')}

    Write a concise summary  in plain English explaining what went wrong
    and what action was taken, suitable for a non-technical stakeholder reading a dashboard.
    Do not repeat the raw field names, write it as natural prose.   
    """

    response = llm.invoke(prompt)
    state["incident_summary"] = response.content

    print(f"[Summarizer] Generated summary for job '{state.get('job_name')}'")
    return state