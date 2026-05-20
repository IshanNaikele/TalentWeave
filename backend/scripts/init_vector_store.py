import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.rag_engine import build_vector_store

if __name__ == "__main__":
    print("🚀 Initializing TalentWeave Knowledge Base...")
    build_vector_store()
    print("🎉 Knowledge base initialization complete.")