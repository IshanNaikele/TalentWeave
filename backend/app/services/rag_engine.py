import os
import json
from pathlib import Path
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from dotenv import load_dotenv

load_dotenv()

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
POLICIES_DIR = BASE_DIR / "backend" / "data" / "company_policies"
VECTOR_STORE_DIR = BASE_DIR / "backend" / "data" / "vector_store"

# Role mapping based on filename
ROLE_MAPPING = {
    "engineering_setup_guide.md": "software_engineer",
    "sales_crm_playbook.md": "sales_team",
}

def get_embedding_model():
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

def load_and_chunk_documents() -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=30
    )

    all_chunks = []

    for filename, target_role in ROLE_MAPPING.items():
        filepath = POLICIES_DIR / filename
        if not filepath.exists():
            print(f"⚠️ File not found: {filepath}")
            continue

        raw_text = filepath.read_text(encoding="utf-8")
        chunks = splitter.split_text(raw_text)

        for chunk in chunks:
            doc = Document(
                page_content=chunk,
                metadata={"target_role": target_role, "source": filename}
            )
            all_chunks.append(doc)

        print(f"✅ Loaded {len(chunks)} chunks from {filename} → role: {target_role}")

    return all_chunks


def build_vector_store():
    print("🔧 Building FAISS vector store...")
    documents = load_and_chunk_documents()

    if not documents:
        print("❌ No documents found. Aborting.")
        return

    embeddings = get_embedding_model()
    vector_store = FAISS.from_documents(documents, embeddings)

    VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
    vector_store.save_local(str(VECTOR_STORE_DIR))
    print(f"✅ Vector store saved to: {VECTOR_STORE_DIR}")


def load_vector_store() -> FAISS:
    embeddings = get_embedding_model()
    vector_store = FAISS.load_local(
        str(VECTOR_STORE_DIR),
        embeddings,
        allow_dangerous_deserialization=True
    )
    return vector_store


def search_by_role(query: str, role: str, k: int = 4) -> list[Document]:
    vector_store = load_vector_store()
    all_results = vector_store.similarity_search(query, k=20)

    filtered = [
        doc for doc in all_results
        if doc.metadata.get("target_role") == role
    ]

    return filtered[:k]