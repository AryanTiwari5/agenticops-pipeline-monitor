from langgraph.graph import StateGraph, END
from state import PipelineState
from agents import log_analyzer_node, doc_retriever_node, remediation_node, summarize_incident_node

def route_after_analysis(state: PipelineState) -> str:
    """
    Decides what happens after the log analyzer runs.
    Reads state['next_step'] which log_analyzer_node already sets.
    """
    next_step = state.get("next_step")
    if next_step == "no_failures":
        return "end"
    return "retrieve_runbook"

def route_after_retrieval(state: PipelineState) -> str:
    """
    Decides what happens after the document retriever runs.
    If no runbook was found, skip remediation and go straight to escalation.
    """
    next_step = state.get("next_step")
    if next_step == "escalate":
        return "escalate"
    return "remediate"

def escalate_node(state: PipelineState) -> PipelineState:
    """
    Fallback node for when no runbook is found.
    In a fuller version, this could notify a human (Slack/email).
    For now, it just logs the escalation clearly.
    """
    state["recommended_action"] = "escalate"
    state["action_taken"] = "Escalated: no matching runbook found"
    print(f"[Escalate] Job '{state.get('job_name')}' escalated — no runbook match")
    return state

def build_graph():
    graph = StateGraph(PipelineState)

    graph.add_node("analyze", log_analyzer_node)
    graph.add_node("retrieve_runbook", doc_retriever_node)
    graph.add_node("remediate", remediation_node)
    graph.add_node("escalate", escalate_node)
    graph.add_node("summarize", summarize_incident_node)   # NEW

    graph.set_entry_point("analyze")

    graph.add_conditional_edges(
        "analyze",
        route_after_analysis,
        {
            "retrieve_runbook": "retrieve_runbook",
            "end": END,
        },
    )

    graph.add_conditional_edges(
        "retrieve_runbook",
        route_after_retrieval,
        {
            "remediate": "remediate",
            "escalate": "escalate",
        },
    )

    # Both remediate and escalate now flow into summarize, instead of straight to END
    graph.add_edge("remediate", "summarize")
    graph.add_edge("escalate", "summarize")
    graph.add_edge("summarize", END)

    return graph.compile()
