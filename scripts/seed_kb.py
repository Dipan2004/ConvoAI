from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.embedding_service import EmbeddingService
from services.vector_db_service import VectorDBService


def main() -> None:
    chunks = [
        "Basic Plan costs $29/month and includes 10 videos/month with 720p export.",
        "Pro Plan costs $79/month and includes unlimited videos, 4K export, and AI captions.",
        "No refunds are available after 7 days.",
        "Pro plan includes 24/7 support.",
        "Basic plan has email support only.",
    ]
    metadata = [{"source": "autostream.md"} for _ in chunks]
    ids = [
        "autostream-basic-plan",
        "autostream-pro-plan",
        "autostream-refund-policy",
        "autostream-pro-support",
        "autostream-basic-support",
    ]

    vector_db = VectorDBService(embedding_service=EmbeddingService())
    vector_db.add_documents(docs=chunks, metadatas=metadata, ids=ids)
    print(f"Seeded {len(chunks)} knowledge base chunks.")


if __name__ == "__main__":
    main()
