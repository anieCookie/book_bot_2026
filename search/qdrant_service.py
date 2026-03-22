from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from config import QDRANT_PATH, QDRANT_COLLECTION, EMBEDDING_DIM

print("Запуск qdrant")
qdrant_client = QdrantClient(path=QDRANT_PATH)
print("Qdrant готов")
print()


def init_qdrant_collection():

    collections = qdrant_client.get_collections().collections

    if not any(c.name == QDRANT_COLLECTION for c in collections):

        qdrant_client.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=VectorParams(
                size=EMBEDDING_DIM,
                distance=Distance.COSINE
            )
        )


def add_to_qdrant(point_id, embedding, payload):

    qdrant_client.upsert(
        collection_name=QDRANT_COLLECTION,
        points=[
            PointStruct(
                id=point_id,
                vector=embedding.tolist(),
                payload=payload
            )
        ]
    )


def search_qdrant(embedding, limit=10):

    return qdrant_client.search(
        collection_name=QDRANT_COLLECTION,
        query_vector=embedding.tolist(),
        limit=limit
    )