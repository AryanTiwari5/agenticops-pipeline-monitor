import os
from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import MarkdownTextSplitter
from langchain_postgres import PGVector
from langchain_huggingface import HuggingFaceEmbeddings  # updated import, fixes the deprecation warning too

load_dotenv()

# Build a psycopg3-specific connection string for PGVector
PG_USER = os.getenv("POSTGRES_USER")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD")
PG_DB = os.getenv("POSTGRES_DB")
PG_CONNECTION = f"postgresql+psycopg://{PG_USER}:{PG_PASSWORD}@postgres:5432/{PG_DB}"

COLLECTION_NAME = "runbooks"

def main():
    print("Loading runbook documents...")
    loader = DirectoryLoader("runbooks", glob="*.md", loader_cls=TextLoader)
    documents = loader.load()
    print(f"Loaded {len(documents)} documents")

    splitter = MarkdownTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(documents)
    print(f"Split into {len(chunks)} chunks")

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    print("Storing embeddings in Postgres (pgvector)...")
    vectorstore = PGVector.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        connection=PG_CONNECTION,
        use_jsonb=True,
    )
    print("Done! Runbooks are now searchable via pgvector.")

if __name__ == "__main__":
    main()