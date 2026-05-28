"""LLM 호출 래퍼 - 오픈AI / 앤트로픽 / 미스트랄 지원. usage 추적 포함."""

import logging

from common.config import settings
from common.usage import get_tracker, stopwatch

logger = logging.getLogger(__name__)


SYSTEM_PROMPT_KOR = (
    "당신은 주어진 컨텍스트를 사용해 사용자의 질문에 답하는 어시스턴트입니다. "
    "컨텍스트에 답이 없으면 '주어진 자료로는 답할 수 없습니다'라고 말하세요. "
    "근거 없는 추측은 금지합니다."
)

PROMPT_TEMPLATE = (
    "다음 컨텍스트를 참고해 질문에 답하세요.\n\n"
    "[컨텍스트]\n{context}\n\n"
    "[질문]\n{query}\n\n"
    "[답변]"
)


class GenerationLLM:
    """오픈AI / 앤트로픽 / 미스트랄 LLM 호출. 호출마다 usage 추적."""

    def __init__(self, model: str | None = None, provider: str | None = None):
        self.provider = provider or settings.llm_provider
        self.model = model or settings.gen_llm_model
        self._tracker = get_tracker()

        if self.provider == "openai":
            from openai import OpenAI

            self.client = OpenAI(api_key=settings.openai_api_key)
        elif self.provider == "anthropic":
            from anthropic import Anthropic

            self.client = Anthropic(api_key=settings.anthropic_api_key)
        elif self.provider == "mistral":
            from mistralai import Mistral

            self.client = Mistral(api_key=settings.mistral_api_key)
        else:
            raise ValueError(f"unsupported provider: {self.provider}")

    def _call_openai(self, system: str, user: str, temperature: float) -> str:
        with stopwatch() as sw:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=temperature,
            )
        usage = resp.usage
        self._tracker.record(
            model=self.model,
            in_tok=getattr(usage, "prompt_tokens", 0) if usage else 0,
            out_tok=getattr(usage, "completion_tokens", 0) if usage else 0,
            elapsed=sw.elapsed,
        )
        return resp.choices[0].message.content or ""

    def _call_anthropic(self, system: str, user: str, temperature: float) -> str:
        with stopwatch() as sw:
            resp = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system,
                messages=[{"role": "user", "content": user}],
                temperature=temperature,
            )
        usage = resp.usage
        self._tracker.record(
            model=self.model,
            in_tok=getattr(usage, "input_tokens", 0) if usage else 0,
            out_tok=getattr(usage, "output_tokens", 0) if usage else 0,
            elapsed=sw.elapsed,
        )
        return resp.content[0].text

    def _call_mistral(self, system: str, user: str, temperature: float) -> str:
        with stopwatch() as sw:
            resp = self.client.chat.complete(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=temperature,
            )
        usage = resp.usage
        self._tracker.record(
            model=self.model,
            in_tok=getattr(usage, "prompt_tokens", 0) if usage else 0,
            out_tok=getattr(usage, "completion_tokens", 0) if usage else 0,
            elapsed=sw.elapsed,
        )
        return resp.choices[0].message.content or ""

    def generate(self, query: str, contexts: list[str], system: str | None = None) -> str:
        ctx_text = "\n\n".join(f"({i + 1}) {c}" for i, c in enumerate(contexts))
        user = PROMPT_TEMPLATE.format(context=ctx_text, query=query)
        sys = system or SYSTEM_PROMPT_KOR
        return self._dispatch(sys, user, temperature=0.1)

    def raw(self, system: str, user: str, temperature: float = 0.3) -> str:
        return self._dispatch(system, user, temperature)

    def _dispatch(self, system: str, user: str, temperature: float) -> str:
        if self.provider == "openai":
            return self._call_openai(system, user, temperature)
        if self.provider == "anthropic":
            return self._call_anthropic(system, user, temperature)
        if self.provider == "mistral":
            return self._call_mistral(system, user, temperature)
        raise ValueError(f"unsupported provider: {self.provider}")
