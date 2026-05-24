"""
This file is used to call the LLM.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import anthropic as anthropic_types
    import google.generativeai as genai_types
    import openai as openai_types


class LLMAdapter(ABC):
    """Provider-specific client; all implementations return plain text."""

    @abstractmethod
    def complete(self, prompt: str) -> str:
        ...


class AnthropicAdapter(LLMAdapter):
    DEFAULT_MODEL = "claude-haiku-4-5"

    def __init__(self, model: str | None = None, api_key: str | None = None):
        import anthropic

        self._client: anthropic_types.Anthropic = anthropic.Anthropic(
            api_key=api_key or os.getenv("ANTHROPIC_API_KEY")
        )
        self._model = model or self.DEFAULT_MODEL

    def complete(self, prompt: str) -> str:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text


class OpenAIAdapter(LLMAdapter):
    DEFAULT_MODEL = "gpt-5.4-mini-2026-03-17"

    def __init__(self, model: str | None = None, api_key: str | None = None):
        import openai

        self._client: openai_types.OpenAI = openai.OpenAI(
            api_key=api_key or os.getenv("OPENAI_API_KEY")
        )
        self._model = model or self.DEFAULT_MODEL

    def complete(self, prompt: str) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.choices[0].message.content
        if content is None:
            raise ValueError("OpenAI returned empty content")
        return content


class GeminiAdapter(LLMAdapter):
    DEFAULT_MODEL = "gemini-3.5-flash"

    def __init__(self, model: str | None = None, api_key: str | None = None):
        import google.generativeai as genai

        genai.configure(api_key=api_key or os.getenv("GEMINI_API_KEY"))
        self._model: genai_types.GenerativeModel = genai.GenerativeModel(
            model or self.DEFAULT_MODEL
        )

    def complete(self, prompt: str) -> str:
        response = self._model.generate_content(prompt)
        text = response.text
        if not text:
            raise ValueError("Gemini returned empty content")
        return text


_ADAPTERS: dict[str, type[LLMAdapter]] = {
    "anthropic": AnthropicAdapter,
    "openai": OpenAIAdapter,
    "gemini": GeminiAdapter,
}


class LLMCaller:
    def __init__(self, service_provider: str | None = None):
        provider = service_provider or os.getenv("LLM_PROVIDER", "anthropic")
        adapter_cls = _ADAPTERS.get(provider)
        if adapter_cls is None:
            raise ValueError(f"Invalid service provider: {provider}")
        self.service_provider = provider
        self._adapter = adapter_cls()

    def call(self, prompt: str) -> str:
        return self._adapter.complete(prompt)
