from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class PipelineLog(Base):
    """
    One row = one log line/event from the ETL pipeline.
    This is what the Log Analyzer Agent will read and reason over.
    """
    __tablename__ = "pipeline_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)       # e.g. "SUCCESS", "FAILED", "RUNNING"
    message = Column(Text, nullable=True)               # raw log message / error text
    timestamp = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<PipelineLog {self.job_name} - {self.status} @ {self.timestamp}>"