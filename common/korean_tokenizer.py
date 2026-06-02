"""한국어 BM25용 Kiwi 형태소 분석기 래퍼."""

import re
from functools import lru_cache


@lru_cache(maxsize=1)
def _get_kiwi():
    from kiwipiepy import Kiwi

    return Kiwi()


_HANGUL_RE = re.compile(r"[가-힯]")


def tokenize_korean(text: str) -> list[str]:
    """한국어 텍스트를 명사/동사/형용사 어간 위주로 토큰화.

    BM25에 넣을 토큰만 추출 - 조사/어미 제거로 어휘 일치율을 높임.
    """
    kiwi = _get_kiwi()
    tokens = kiwi.tokenize(text)
    keep_tags = {"NNG", "NNP", "NNB", "VV", "VA", "MAG", "SL", "SN"}
    return [t.form for t in tokens if t.tag in keep_tags]


def tokenize_mixed(text: str) -> list[str]:
    """한/영 혼합 텍스트용 - 한국어 부분은 Kiwi, 영어 부분은 공백 분할."""
    if _HANGUL_RE.search(text):
        return tokenize_korean(text)
    return [w.lower() for w in re.findall(r"\w+", text)]
