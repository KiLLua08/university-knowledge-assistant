"""Client for the local LM Studio OpenAI-compatible chat completion API.

There is no model object to load on our side: LM Studio hosts Qwen. We create
one reusable HTTP client per service instance and send ordinary HTTP requests,
so no heavy work is repeated per question.
"""

from __future__ import annotations

import httpx

from ..config import Settings, get_settings


class LLMError(Exception):
    """Base class for language-model failures."""


class LLMConnectionError(LLMError):
    """LM Studio could not be reached."""


class LLMTimeoutError(LLMError):
    """LM Studio did not answer in time."""


class LLMHTTPError(LLMError):
    """LM Studio answered with an HTTP error status."""


class LLMResponseError(LLMError):
    """LM Studio answered with an unusable response body."""


class LLMService:
    """Small, reusable wrapper around ``POST /v1/chat/completions``."""

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        client: httpx.Client | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self._owns_client = client is None
        self._client = client or httpx.Client(
            base_url=self.settings.llm_base_url.rstrip("/"),
            timeout=httpx.Timeout(self.settings.llm_timeout_seconds, connect=5.0),
            headers={
                "Authorization": f"Bearer {self.settings.llm_api_key}",
                "Content-Type": "application/json",
            },
        )

    def generate_answer(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """Send one chat request and return the assistant's text.

        Args:
            system_prompt: Grounding instructions for the model.
            user_prompt: The student question plus retrieved context.
            temperature: Optional per-call override of the configured value.
            max_tokens: Optional per-call override of the configured limit.

        Raises:
            LLMConnectionError: Connection to LM Studio failed.
            LLMTimeoutError: The request timed out.
            LLMHTTPError: LM Studio returned a non-2xx status.
            LLMResponseError: The response was invalid or empty.
        """
        payload = {
            "model": self.settings.llm_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": (self.settings.llm_temperature if temperature is None else temperature),
            "max_tokens": (self.settings.llm_max_tokens if max_tokens is None else max_tokens),
            "stream": False,
        }

        try:
            response = self._client.post("/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()
        except httpx.TimeoutException as exc:
            raise LLMTimeoutError("LM Studio did not respond in time") from exc
        except (httpx.ConnectError, httpx.NetworkError) as exc:
            raise LLMConnectionError(
                f"Could not connect to LM Studio at {self.settings.llm_base_url}"
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise LLMHTTPError(f"LM Studio returned HTTP {exc.response.status_code}") from exc
        except ValueError as exc:
            raise LLMResponseError("LM Studio returned invalid JSON") from exc

        return self._extract_content(data)

    @staticmethod
    def _extract_content(data: object) -> str:
        """Pull the first assistant message out of an OpenAI-style response."""
        if not isinstance(data, dict):
            raise LLMResponseError("LM Studio response is not a JSON object")

        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            raise LLMResponseError("LM Studio response contains no choices")

        first = choices[0]
        message = first.get("message") if isinstance(first, dict) else None
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str) or not content.strip():
            if isinstance(message, dict) and message.get("reasoning_content"):
                raise LLMResponseError(
                    "LM Studio returned only reasoning content; " "increase LLM_MAX_TOKENS"
                )
            raise LLMResponseError("LM Studio response contains no assistant text")

        return content.strip()

    def close(self) -> None:
        """Close the HTTP client if this service created it."""
        if self._owns_client:
            self._client.close()
