# Schema Mismatch Errors

## Symptom
Job fails with: "Schema mismatch: expected column 'user_id' not found in source file"

## Likely Causes
- Upstream source changed its file/table structure without notice
- A column was renamed, dropped, or reordered at the source
- Wrong file version or an incomplete file was picked up

## Remediation Steps
1. Do NOT blindly retry — retrying will not fix a structural mismatch.
2. Inspect the actual source file/table schema and compare it to what the pipeline expects.
3. Check whether this was a planned schema change from the upstream team.
4. If planned, update the pipeline's expected schema definition.
5. If unplanned, alert the upstream data owner before proceeding.

## Automated Action
Do not auto-retry. Flag for human review and log the exact schema diff if available.