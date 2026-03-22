import chardet

file_cache = {}


def detect_encoding(path):
    with open(path, "rb") as f: raw = f.read()
    return chardet.detect(raw)["encoding"] or "utf-8"


def read_file(path):
    if path in file_cache:
        return file_cache[path]
    enc = detect_encoding(path)

    with open(path, "r", encoding=enc) as f: text = f.read()
    file_cache[path] = text
    return text


def read_text_range(path, start, end):
    text = read_file(path)
    return text[start:end]