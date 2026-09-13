from typing import TypedDict, Optional


class PipelineState(TypedDict):
    job_id: Optional[int]
    job_name: Optional[str]
    status: Optional[str]
    error_message: Optional[str]


    #Log Analyzer output
    error_category: Optional[str]
    analysis_confidence: Optional[str]


    #Doc retriever output
    runbook_content: Optional[str]
    retrieval_found: Optional[bool]

    #Remediation output
    recommended_action: Optional[str]   # e.g. "retry", "escalate", "no_action"
    action_taken: Optional[str]
    retry_count: Optional[int]

    # Supervisor control
    next_step: Optional[str]
