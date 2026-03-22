import numpy as np
from sentence_transformers import SentenceTransformer

print("Загрузка модели эмбеддингов")
embedding_model = SentenceTransformer("cointegrated/rubert-tiny2")
print("Модель загружена")
print()


def get_embedding(text: str):
    return embedding_model.encode(text, normalize_embeddings=True)


def cosine_similarity(v1, v2):
    return float(np.dot(v1, v2))
