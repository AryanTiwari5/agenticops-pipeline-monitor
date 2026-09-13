# Upstream Dependency Errors

## Symptom
Job fails with: "Job failed: upstream dependency 'raw_events' not yet available"

## Likely Causes
- The upstream job hasn't finished running yet (timing/scheduling issue)
- The upstream job itself failed
- Dependency configuration is incorrect

## Remediation Steps
1. Check whether the upstream job ('raw_events') completed successfully.
2. If the upstream job is still running, wait and retry after a delay.
3. If the upstream job failed, resolve that failure first — this job cannot succeed independently.

## Automated Action
Retry with a delay (e.g., 60s) up to 3 times before escalating.