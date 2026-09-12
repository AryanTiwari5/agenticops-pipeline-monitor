import random
import time
from datetime import datetime
from db import init_db, get_session
from models import PipelineLog

# Fake jobs your "pipeline" runs
JOBS = ["extract_sales_data", "transform_customer_records", "load_to_warehouse", "sync_inventory"]

# Realistic failure messages, so later agents have something meaningful to analyze
FAILURE_MESSAGES = [
    "Connection timeout after 30s while reaching source database",
    "Schema mismatch: expected column 'user_id' not found in source file",
    "Out of memory while processing batch of 500,000 rows",
    "Permission denied writing to target S3 bucket",
    "Job failed: upstream dependency 'raw_events' not yet available",
]

def run_job(job_name: str):
    """Simulates running one job. ~70% success, ~30% failure."""
    success = random.random() > 0.3

    if success:
        status = "SUCCESS"
        message = f"{job_name} completed successfully"
    else:
        status = "FAILED"
        message = random.choice(FAILURE_MESSAGES)

    return status, message

def main():
    print("Starting ETL simulator...")
    init_db()  # make sure tables exist

    while True:
        job_name = random.choice(JOBS)
        status, message = run_job(job_name)

        session = get_session()
        log_entry = PipelineLog(
            job_name=job_name,
            status=status,
            message=message,
            timestamp=datetime.utcnow(),
        )
        session.add(log_entry)
        session.commit()
        session.close()

        print(f"[{datetime.utcnow()}] {job_name} -> {status}: {message}")

        time.sleep(10)  # wait 10 seconds before the next job

if __name__ == "__main__":
    main()