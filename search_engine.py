import os
from typing import List, Dict, Optional

from config import BOOKS_DIR, SIMILARITY_THRESHOLD
from search.embeddings import get_embedding, embedding_model, cosine_similarity
from search.qdrant_service import search_qdrant
from text.text_utils import clean_query, split_into_chunks
from text.file_utils import read_text_range


def find_relevant_chunks(user_question: str, limit: int = 10) -> Optional[List[Dict]]:
    cleaned_question = clean_query(user_question)

    query_emb = get_embedding(cleaned_question)
    results = search_qdrant(query_emb)

    if not results or results[0].score < SIMILARITY_THRESHOLD:
        return None

    # Скользящее окно внутри каждого абзаца
    all_chunks = []
    for r in results:
        p = r.payload
        path = os.path.join(BOOKS_DIR, f"{p['book_uuid']}.txt")
        para_text = read_text_range(path, p['char_start'], p['char_end'])

        chunks = split_into_chunks(para_text, p['char_start'])
        embs = embedding_model.encode(
            [c['text'] for c in chunks],
            normalize_embeddings=True
        )

        for i, c in enumerate(chunks):
            sim = cosine_similarity(query_emb, embs[i])
            all_chunks.append({
                'text': c['text'],
                'sim': sim,
                'book_title': p['book_title'],
                'chapter': p.get('chapter_number'),
                'char_start': c['char_start'],
                'char_end': c['char_end'],
                'file_path': path
            })

    all_chunks.sort(key=lambda x: x['sim'], reverse=True)
    top_chunks = all_chunks[:limit]

    if not top_chunks or top_chunks[0]['sim'] < 0.3:
        return None

    return top_chunks


def format_citation(chunk: Dict) -> str:
    chapter = chunk.get('chapter')

    if chapter == 0:
        return f"📖 <b>{chunk['book_title']}</b>\n{chunk['text']}"
    else:
        return f"📖 <b>{chunk['book_title']}</b> (Глава {chapter})\n{chunk['text']}"


def format_citations(chunks: List[Dict]) -> str:
    return "\n\n".join([format_citation(c) for c in chunks])