from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional

from google import genai
from google.genai import types

from polaris_studio.agent.schemas import ChatEvent


class AIBackend(ABC):
    @abstractmethod
    def chat(
        self,
        messages: List[Dict[str, Any]],
        system: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        stream: bool = True,
    ) -> AsyncIterator[ChatEvent]: ...


class GeminiBackend(AIBackend):
    def __init__(self, api_key: str, model: str = "gemma-4-31b-it") -> None:
        self._api_key = api_key
        self._model = model
        self._client: Optional[genai.Client] = None

    def _ensure_client(self) -> genai.Client:
        if self._client is None:
            self._client = genai.Client(api_key=self._api_key)
        return self._client

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        system: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        stream: bool = True,
    ) -> AsyncIterator[ChatEvent]:
        client = self._ensure_client()

        genai_contents: List[types.Content] = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            parts: List[types.Part] = []

            if role == "tool":
                genai_role = "user"
                parts.append(
                    types.Part.from_function_response(
                        name=msg.get("tool_call_id", ""),
                        response={"content": msg.get("content", "")},
                    )
                )
            elif role == "assistant":
                genai_role = "model"
                if content:
                    parts.append(types.Part.from_text(text=content))
                for tc in msg.get("tool_calls", []):
                    fn = tc.get("function", {})
                    args_raw = fn.get("arguments", "{}")
                    args = json.loads(args_raw) if isinstance(args_raw, str) else args_raw
                    parts.append(
                        types.Part.from_function_call(
                            name=fn.get("name", ""),
                            args=args,
                        )
                    )
                for tr in msg.get("tool_results", []):
                    parts.append(
                        types.Part.from_function_response(
                            name=tr.get("name", ""),
                            response={"content": tr.get("content", "")},
                        )
                    )
            else:
                genai_role = "user"
                if content:
                    parts.append(types.Part.from_text(text=content))

            if parts:
                genai_contents.append(types.Content(role=genai_role, parts=parts))

        config = types.GenerateContentConfig(
            temperature=0.7,
            max_output_tokens=8192,
        )

        if system:
            config.system_instruction = system

        if tools:
            declarations = []
            for t in tools:
                declarations.append(
                    types.FunctionDeclaration(
                        name=t.get("name", ""),
                        description=t.get("description", ""),
                        parameters=t.get("input_schema", {"type": "object", "properties": {}}),
                    )
                )
            if declarations:
                config.tools = [types.Tool(function_declarations=declarations)]

        try:
            response_stream = await client.aio.models.generate_content_stream(
                model=self._model,
                contents=genai_contents,  # type: ignore[arg-type]
                config=config,
            )
            async for chunk in response_stream:
                if chunk.text:
                    yield ChatEvent(type="token", text=chunk.text)
                if chunk.candidates:
                    for candidate in chunk.candidates:
                        if candidate.content and candidate.content.parts:
                            for part in candidate.content.parts:
                                if part.function_call:
                                    fc = part.function_call
                                    yield ChatEvent(
                                        type="tool_use",
                                        tool_name=fc.name or "",
                                        tool_args=fc.args or {},
                                    )
        except Exception as e:
            yield ChatEvent(type="error", message=f"Gemini API error: {e}")

        yield ChatEvent(type="done")


class AIBackendRouter:
    def __init__(self) -> None:
        self._api_key: Optional[str] = None
        self._model: str = "gemma-4-31b-it"
        self._backend: Optional[GeminiBackend] = None

    def configure(self, api_key: Optional[str] = None, model: str = "gemma-4-31b-it") -> None:
        self._api_key = api_key
        self._model = model
        self._backend = None

    def get_backend(self) -> Optional[GeminiBackend]:
        if self._backend is not None:
            return self._backend
        if self._api_key:
            self._backend = GeminiBackend(self._api_key, self._model)
            return self._backend
        return None

    async def probe(self) -> bool:
        if not self._api_key:
            return False
        try:
            client = genai.Client(api_key=self._api_key)
            await client.aio.models.list()
            return True
        except Exception:
            return False
