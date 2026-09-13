# Connection Timeout Errors

## Symptom
Job fails with: "Connection timeout after 30s while reaching source database"

## Likely Causes
- Source database is under heavy load or unresponsive
- Network partition between the pipeline and the database host
- Firewall or security group blocking the connection
- Database connection pool exhausted

## Remediation Steps
1. Retry the job once — transient network blips are common and often self-resolve.
2. If retry fails, check the source database's health/load metrics.
3. Verify network connectivity between the pipeline container and the database host.
4. Increase the connection timeout setting if the source system is known to be slow under load.
5. If the issue persists after 2 retries, escalate to the infrastructure team.

## Automated Action
Restart the failing job container and retry up to 2 times before escalating. 