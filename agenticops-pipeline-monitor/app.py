import streamlit as st
from db import init_db, get_session
from models import PipelineLog

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