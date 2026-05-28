"""문서 청크 분할 유틸 - 단순 / 시멘틱 / 부모-자식."""

from dataclasses import dataclass


@dataclass
class Chunk:
    text: str
    metadata: dict


def simple_chunk(text: str, chunk_size: int = 400, overlap: int = 50) -> list[str]:
    """문자 수 기준 슬라이딩 윈도우. 가장 단순한 베이스라인."""
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be larger than overlap")
    step = chunk_size - overlap
    return [text[i : i + chunk_size] for i in range(0, len(text), step) if text[i : i + chunk_size]]


def semantic_chunk(text: str, max_chars: int = 600) -> list[str]:
    """문단/문장 경계를 우선시하는 청크. 간단 휴리스틱.

    1. 빈 줄로 문단을 나눈다
    2. 문단을 max_chars까지 누적
    3. 문단 자체가 max_chars를 넘으면 문장(. ? ! 。 ?) 단위로 추가 분할
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    buf = ""

    def flush():
        nonlocal buf
        if buf.strip():
            chunks.append(buf.strip())
        buf = ""

    for para in paragraphs:
        if len(para) > max_chars:
            flush()
            current = ""
            sentences = _split_sentences(para)
            for s in sentences:
                if len(current) + len(s) > max_chars and current:
                    chunks.append(current.strip())
                    current = s
                else:
                    current += " " + s if current else s
            if current.strip():
                chunks.append(current.strip())
            continue

        if len(buf) + len(para) > max_chars:
            flush()
        buf = (buf + "\n\n" + para) if buf else para

    flush()
    return chunks


def _split_sentences(text: str) -> list[str]:
    out: list[str] = []
    cur = ""
    enders = {".", "?", "!", "。", "?"}
    for ch in text:
        cur += ch
        if ch in enders:
            out.append(cur.strip())
            cur = ""
    if cur.strip():
        out.append(cur.strip())
    return out


def parent_child_chunk(
    text: str,
    parent_size: int = 1200,
    child_size: int = 250,
) -> list[tuple[str, list[str]]]:
    """부모-자식 청크 생성.

    반환: [(parent_text, [child_text, ...]), ...]
    부모는 길게 잡아 컨텍스트 보존, 자식은 작게 잘라 검색 정밀도 향상에 사용.
    """
    parents = simple_chunk(text, chunk_size=parent_size, overlap=100)
    result: list[tuple[str, list[str]]] = []
    for p in parents:
        children = simple_chunk(p, chunk_size=child_size, overlap=30)
        result.append((p, children))
    return result
