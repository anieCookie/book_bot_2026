import re
from nltk.stem.snowball import SnowballStemmer

stemmer = SnowballStemmer("russian")


def normalize_title(title):
    title = title.lower()
    title = re.sub(r"[^\w\s]", "", title)

    words = title.split()
    words = [stemmer.stem(w) for w in words]
    return " ".join(words)


def clean_query(q):
    stop_words = [
        "где", "найди", "найти", "покажи",
        "скажи", "расскажи", "где говорится",
        "что", "как", "когда", "почему", "про", "о"
    ]

    q = q.lower()
    for w in stop_words:
        q = re.sub(rf"\b{w}\b", "", q)

    q = re.sub(r"\s+", " ", q).strip()
    return q


def split_text_to_paragraphs(text):
    text = text.replace("\r\n", "\n")
    parts = re.split(r"\n\s*\n", text)

    paragraphs = []
    pos = 0

    for part in parts:
        stripped = part.strip()
        if len(stripped) > 20:
            start = text.index(stripped, pos)
            end = start + len(stripped)

            paragraphs.append({
                "text": stripped,
                "char_start": start,
                "char_end": end
            })
        pos += len(part)

    return paragraphs


def split_into_chunks(text, char_start):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    chunks = []
    for i in range(0, len(sentences), 2):
        chunk = " ".join(sentences[i:i + 2])
        pos = text.find(chunk)

        start = char_start + pos
        end = start + len(chunk)

        chunks.append({
            "text": chunk,
            "char_start": start,
            "char_end": end
        })

    return chunks
