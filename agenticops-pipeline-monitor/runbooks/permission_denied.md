# Permission Denied Errors

## Symptom
Job fails with: "Permission denied writing to target S3 bucket"

## Likely Causes
- IAM role or credentials lack write access to the target bucket
- Bucket policy was changed
- Credentials expired or were rotated without updating the pipeline

## Remediation Steps
1. Do NOT retry blindly — a permissions issue will not resolve itself.
2. Verify the pipeline's IAM role/credentials are current and have write access.
3. Check for recent changes to the bucket policy or IAM permissions.
4. Rotate/update credentials if expired.

## Automated Action
Do not auto-retry. Flag for human review — this is a security-sensitive failure type.