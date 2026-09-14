import streamlit as st
from db import init_db, get_session
from models import PipelineLog
from state import PipelineState
st.title("AgenticOps Pipeline Monitor")

init_db()
st.write("Database tables initialized.")


if st.button("Insert test log"):
    session = get_session()
    new_log = PipelineLog(job_name = "Test job", status = "Success", message = "This is a test row.")
    session.add(new_log)
    session.commit()
    session.close()
    st.write("Test row inserted.")

if st.button("Show all logs"):
    session = get_session()
    logs = session.query(PipelineLog).all()
    session.close()
    for log in logs:
        st.write(f"{log.id} | {log.job_name} | {log.status} |  {log.timestamp}")

from agents import log_analyzer_node, doc_retriever_node

if st.button("Test Log Analyzer + Retriever"):
    state = {}
    state = log_analyzer_node(state)
    state = doc_retriever_node(state)
    st.json(state)

from agents import log_analyzer_node, doc_retriever_node, remediation_node

if st.button("Test Full Agent Flow"):
    state = {}
    state = log_analyzer_node(state)
    state = doc_retriever_node(state)
    state = remediation_node(state)
    st.json(state)

from graph import build_graph

pipeline_graph = build_graph()

if st.button("Run Agent Graph"):
    initial_state: PipelineState = {
        "job_id": None, "job_name": None, "status": None, "error_message": None,
        "error_category": None, "analysis_confidence": None, "runbook_content": None,
        "retrieval_found": None, "recommended_action": None, "action_taken": None,
        "retry_count": 0, "next_step": None, "incident_summary": None,
    }
    final_state = pipeline_graph.invoke(initial_state)

    st.subheader("Incident Summary")
    st.write(final_state.get("incident_summary", "No summary generated."))

    with st.expander("Full agent state (debug)"):
        st.json(final_state)