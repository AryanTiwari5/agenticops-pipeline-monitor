# Out of Memory Errors

## Symptom
Job fails with: "Out of memory while processing batch of 500,000 rows"

## Likely Causes
- Batch size too large for the container's allocated memory
- A memory leak in the transformation logic
- Unexpectedly large input data volume compared to normal runs

## Remediation Steps
1. Reduce the batch size and retry the job.
2. Check whether the input data volume was abnormally large this run.
3. If this happens repeatedly, increase the container's memory allocation.
4. Review transformation code for unbounded in-memory operations (e.g., loading entire datasets instead of streaming).

## Automated Action
Retry once with a reduced batch size parameter if supported; otherwise escalate.