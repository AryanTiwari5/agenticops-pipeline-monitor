# AgenticOps: Multi-Agent Pipeline Monitor

A multi-agent system that watches a data pipeline, diagnoses failures using retrieval-augmented generation (RAG) over runbook documentation, decides whether to retry or escalate, and writes a plain-English incident summary with an LLM.

Built with **LangGraph, LangChain, PostgreSQL + pgvector, Groq, Streamlit, and Docker Compose**. Everything runs locally on free tools.

---

## What it does

A simulated ETL pipeline runs continuously and fails at random with realistic errors (timeouts, schema mismatches, out-of-memory, permission errors, missing upstream dependencies). When you trigger a run, a LangGraph state machine:

1. **Analyzes** the most recent failed job from Postgres and classifies the error.
2. **Retrieves** the matching runbook using semantic search over pgvector embeddings.
3. **Decides** the action: retry, retry with a reduced batch or delay, or escalate. Safety-sensitive failures (schema changes, permission errors) are never auto-retried.
4. **Logs** the decision back to Postgres as an audit row.
5. **Summarizes** the incident in natural language using a Groq-hosted LLM.

If no relevant runbook is found, the graph routes straight to escalation instead of guessing.

## Architecture

```mermaid
flowchart LR
    ETL[ETL Simulator] -->|writes job logs| PG[(PostgreSQL + pgvector)]
    RB[Runbooks .md] -->|chunk + embed| PG
    UI[Streamlit Dashboard] -->|invoke| G{{LangGraph}}
    G <--> PG
    G -->|summarize| LLM[Groq LLM]
```

### Agent graph

```mermaid
flowchart TD
    S([Start]) --> A[analyze]
    A -->|no failures| E([End])
    A -->|failure found| R[retrieve_runbook]
    R -->|runbook found| M[remediate]
    R -->|no match| X[escalate]
    M --> Z[summarize]
    X --> Z
    Z --> E
```

### Design choices

- **Rules decide, the LLM explains.** Retry-vs-escalate is a deterministic lookup mirroring each runbook's "Automated Action" section. The LLM only writes the summary, so a hallucination can't trigger an unsafe operational action.
- **One database for both jobs.** Postgres holds structured pipeline logs and, through pgvector, the embedded runbooks.
- **Bounded retries.** A max-retry cap forces escalation instead of looping forever.
- **Constrained summaries.** The summarizer prompt forbids claiming an issue was resolved, since the system records a recommended action rather than confirming an outcome.

## Tech stack

| Layer | Tool |
|---|---|
| Agent orchestration | LangGraph, LangChain |
| LLM inference | Groq (free tier) |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (local, CPU) |
| Database + vector store | PostgreSQL 16 + pgvector (`langchain-postgres`) |
| ORM | SQLAlchemy |
| UI | Streamlit |
| Containerization | Docker, Docker Compose |

## Project structure

```
agenticops-pipeline-monitor/
├── app.py                  # Streamlit dashboard
├── graph.py                # LangGraph StateGraph and routing logic
├── agents.py               # Node functions: analyzer, retriever, remediation, summarizer
├── state.py                # Shared PipelineState schema
├── db.py                   # SQLAlchemy engine and sessions
├── models.py               # PipelineLog table
├── ingest_runbooks.py      # Chunks and embeds runbooks into pgvector
├── runbooks/               # One markdown runbook per failure type
├── etl_simulator/          # Standalone container that generates fake job logs
│   ├── simulate.py
│   ├── Dockerfile
│   └── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Getting started

### Prerequisites

- Docker Desktop (with virtualization enabled in BIOS on Windows)
- A free [Groq API key](https://console.groq.com)

### 1. Clone the repo

```bash
git clone https://github.com/<your-username>/agenticops-pipeline-monitor.git
cd agenticops-pipeline-monitor
```

### 2. Create a `.env` file

```
POSTGRES_USER=agenticops
POSTGRES_PASSWORD=change_me
POSTGRES_DB=agenticops
DATABASE_URL=postgresql://agenticops:change_me@postgres:5432/agenticops

GROQ_API_KEY=your_groq_key_here
```

Keep the password identical everywhere it appears. A mismatch between `.env` and `docker-compose.yml` causes "password authentication failed". Never commit `.env`; it is listed in `.gitignore`.

### 3. Build and start

```bash
docker compose up --build -d
```

This starts three services: `agent-app`, `etl-job`, and `postgres`. The first build is slow because of the PyTorch and `sentence-transformers` dependencies.

### 4. Embed the runbooks (one time)

```bash
docker compose exec agent-app python ingest_runbooks.py
```

### 5. Open the dashboard

Go to **http://localhost:8501** and click **Run Agent Graph**. You should see an incident summary, with the full agent state in a collapsible debug section.

### Useful commands

```bash
docker compose ps                      # check service health
docker compose logs -f agent-app       # stream app logs
docker compose restart agent-app       # pick up code changes
docker compose down -v                 # stop and wipe the database volume
```

Run `docker compose down -v` whenever you change `POSTGRES_USER`, `POSTGRES_PASSWORD`, or `POSTGRES_DB`, because Postgres only applies them when it first initializes a fresh volume.

## Example output

> The `extract_sales_data` job failed because it ran out of memory while processing a large batch of rows. The agent recommended retrying with a smaller batch size, per the runbook for this type of error.

*(Add a dashboard screenshot here.)*

## Known limitations

- **Remediation is simulated.** The remediation node records its decision as an audit row in Postgres; it does not yet restart containers or rerun jobs.
- **Error classification is keyword-based.** It is reliable for the known failure patterns but would need an LLM or classifier for open-ended logs.
- **The UI is minimal.** It is a single-button dashboard, not a full monitoring view.
- **Groq model names change.** If you see a `model_not_found` error, check the Groq console for currently available models and update the model name in `_get_llm()` in `agents.py`.

## Roadmap

- [ ] Langfuse tracing for per-node latency, token usage, and decision traces
- [ ] Real remediation through the Docker SDK (restart or rerun failed jobs)
- [ ] Dashboard with job history, failure trends, and agent decision timeline
- [ ] LLM-assisted classification for unknown error types
- [ ] Free-tier cloud deployment

## License

MIT
