"""Production Live API Model Adapter for Hyperscalers and Local Inference Engines.

Supports:
- OpenAI / Azure OpenAI (gpt-4o, gpt-4o-mini, o1)
- Anthropic Claude (claude-3-5-sonnet, claude-3-haiku)
- Google Gemini (gemini-1.5-pro, gemini-1.5-flash)
- Ollama / vLLM / Local / OpenRouter (OpenAI-compatible HTTP endpoints)
"""

from __future__ import annotations
import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional
from .base import ModelAdapter, ModelResponse, ToolCall


class APIModelAdapter(ModelAdapter):
    """Vendor-neutral live HTTP API adapter for major LLM providers."""

    def __init__(
        self,
        provider: str = "openai",
        model_id: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout_seconds: float = 30.0,
        max_retries: int = 2,
    ):
        self.provider = provider.lower()
        self.model_id = model_id
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

        # Resolve API keys from parameters or standard environment variables
        self.api_key = api_key or self._resolve_api_key(self.provider)
        self.base_url = base_url or self._resolve_base_url(self.provider)

    @staticmethod
    def _resolve_api_key(provider: str) -> str:
        if provider in ("openai", "azure"):
            return os.getenv("OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_API_KEY", "")
        elif provider == "anthropic":
            return os.getenv("ANTHROPIC_API_KEY", "")
        elif provider in ("gemini", "google"):
            return os.getenv("GEMINI_API_KEY", "")
        elif provider in ("ollama", "vllm", "local"):
            return os.getenv("LOCAL_API_KEY", "ollama")
        return os.getenv("LLM_API_KEY", "")

    @staticmethod
    def _resolve_base_url(provider: str) -> str:
        if provider == "openai":
            return "https://api.openai.com/v1"
        elif provider == "anthropic":
            return "https://api.anthropic.com/v1"
        elif provider in ("gemini", "google"):
            return "https://generativelanguage.googleapis.com/v1beta"
        elif provider == "ollama":
            return os.getenv("OLLAMA_HOST", "http://localhost:11434/v1")
        elif provider == "vllm":
            return os.getenv("VLLM_HOST", "http://localhost:8000/v1")
        return "https://api.openai.com/v1"

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> ModelResponse:
        """Dispatches request to appropriate provider protocol."""
        if self.provider in ("openai", "ollama", "vllm", "azure", "openrouter"):
            return self._call_openai_compatible(prompt, system_prompt, tools, **kwargs)
        elif self.provider == "anthropic":
            return self._call_anthropic(prompt, system_prompt, tools, **kwargs)
        elif self.provider in ("gemini", "google"):
            return self._call_gemini(prompt, system_prompt, tools, **kwargs)
        else:
            # Fallback to OpenAI-compatible wire format
            return self._call_openai_compatible(prompt, system_prompt, tools, **kwargs)

    def _call_openai_compatible(
        self,
        prompt: str,
        system_prompt: str = "",
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> ModelResponse:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload: Dict[str, Any] = {
            "model": self.model_id,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.0),
        }
        if tools:
            payload["tools"] = [
                {"type": "function", "function": t} for t in tools
            ]

        endpoint = f"{self.base_url.rstrip('/')}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        retries = 0
        last_error = None

        while retries <= self.max_retries:
            start_time = time.perf_counter()
            try:
                req = urllib.request.Request(
                    endpoint,
                    data=json.dumps(payload).encode("utf-8"),
                    headers=headers,
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:
                    latency_ms = (time.perf_counter() - start_time) * 1000.0
                    body = json.loads(response.read().decode("utf-8"))

                    choice = body.get("choices", [{}])[0]
                    message = choice.get("message", {})
                    content = message.get("content") or ""

                    tool_calls = []
                    for raw_tool in message.get("tool_calls", []):
                        fn = raw_tool.get("function", {})
                        args = {}
                        try:
                            args = json.loads(fn.get("arguments", "{}"))
                        except Exception:
                            pass
                        tool_calls.append(
                            ToolCall(
                                name=fn.get("name", "unknown_tool"),
                                arguments=args,
                                call_id=raw_tool.get("id", ""),
                            )
                        )

                    usage = body.get("usage", {})
                    prompt_tokens = usage.get("prompt_tokens", 0)
                    completion_tokens = usage.get("completion_tokens", 0)
                    total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)

                    return ModelResponse(
                        content=content,
                        tool_calls=tool_calls,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        total_tokens=total_tokens,
                        latency_ms=round(latency_ms, 2),
                        retries=retries,
                        model_id=self.model_id,
                    )
            except Exception as e:
                last_error = e
                retries += 1
                time.sleep(1.0 * retries)

        # In case of persistent failure, return structured error response
        return ModelResponse(
            content=f"[API_ERROR: {str(last_error)}]",
            tool_calls=[],
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            latency_ms=0.0,
            retries=retries,
            model_id=self.model_id,
        )

    def _call_anthropic(
        self,
        prompt: str,
        system_prompt: str = "",
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> ModelResponse:
        payload: Dict[str, Any] = {
            "model": self.model_id,
            "max_tokens": kwargs.get("max_tokens", 1024),
            "messages": [{"role": "user", "content": prompt}],
            "temperature": kwargs.get("temperature", 0.0),
        }
        if system_prompt:
            payload["system"] = system_prompt

        endpoint = f"{self.base_url.rstrip('/')}/messages"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }

        start_time = time.perf_counter()
        try:
            req = urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:
                latency_ms = (time.perf_counter() - start_time) * 1000.0
                body = json.loads(response.read().decode("utf-8"))

                content = ""
                for part in body.get("content", []):
                    if part.get("type") == "text":
                        content += part.get("text", "")

                usage = body.get("usage", {})
                prompt_tokens = usage.get("input_tokens", 0)
                completion_tokens = usage.get("output_tokens", 0)

                return ModelResponse(
                    content=content,
                    tool_calls=[],
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens,
                    latency_ms=round(latency_ms, 2),
                    retries=0,
                    model_id=self.model_id,
                )
        except Exception as e:
            return ModelResponse(
                content=f"[ANTHROPIC_API_ERROR: {str(e)}]",
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                latency_ms=0.0,
                retries=1,
                model_id=self.model_id,
            )

    def _call_gemini(
        self,
        prompt: str,
        system_prompt: str = "",
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> ModelResponse:
        endpoint = f"{self.base_url.rstrip('/')}/models/{self.model_id}:generateContent?key={self.api_key}"
        payload: Dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": kwargs.get("temperature", 0.0),
            },
        }
        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

        start_time = time.perf_counter()
        try:
            req = urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:
                latency_ms = (time.perf_counter() - start_time) * 1000.0
                body = json.loads(response.read().decode("utf-8"))

                candidates = body.get("candidates", [{}])
                parts = candidates[0].get("content", {}).get("parts", [{}])
                content = parts[0].get("text", "")

                usage = body.get("usageMetadata", {})
                prompt_tokens = usage.get("promptTokenCount", 0)
                completion_tokens = usage.get("candidatesTokenCount", 0)

                return ModelResponse(
                    content=content,
                    tool_calls=[],
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens,
                    latency_ms=round(latency_ms, 2),
                    retries=0,
                    model_id=self.model_id,
                )
        except Exception as e:
            return ModelResponse(
                content=f"[GEMINI_API_ERROR: {str(e)}]",
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                latency_ms=0.0,
                retries=1,
                model_id=self.model_id,
            )
