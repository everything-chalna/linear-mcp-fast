"""
Official Linear MCP client session manager.

Maintains a long-lived streamable-http MCP client session with reconnect and
single-retry semantics for transient failures.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import threading
import time
from datetime import timedelta
from typing import Any

from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client

logger = logging.getLogger(__name__)

DEFAULT_OFFICIAL_MCP_URL = "https://mcp.linear.app/mcp"


class OfficialToolError(RuntimeError):
    """Raised when the official MCP call fails."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


class OfficialMcpSessionManager:
    """Thread-safe synchronous wrapper around async MCP client session."""

    def __init__(
        self,
        url: str | None = None,
        headers: dict[str, str] | None = None,
        timeout_seconds: float = 30.0,
        sse_read_timeout_seconds: float = 300.0,
        read_timeout_seconds: float = 30.0,
    ):
        self._url = url or os.getenv("LINEAR_OFFICIAL_MCP_URL", DEFAULT_OFFICIAL_MCP_URL)
        self._headers = headers or self._parse_headers_from_env()
        self._timeout_seconds = timeout_seconds
        self._sse_read_timeout_seconds = sse_read_timeout_seconds
        self._read_timeout_seconds = read_timeout_seconds

        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._lock = threading.RLock()

        self._transport_cm: Any = None
        self._session_cm: Any = None
        self._session: ClientSession | None = None

        self._failure_count = 0
        self._last_error: str | None = None
        self._last_connected_at: float | None = None

    @staticmethod
    def _parse_headers_from_env() -> dict[str, str] | None:
        raw = os.getenv("LINEAR_OFFICIAL_MCP_HEADERS")
        if not raw:
            return None
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return {str(k): str(v) for k, v in parsed.items()}
        except Exception:
            logger.warning("Ignoring invalid LINEAR_OFFICIAL_MCP_HEADERS value")
        return None

    def _ensure_loop(self) -> None:
        if self._loop and self._thread and self._thread.is_alive():
            return

        loop = asyncio.new_event_loop()

        def _run_loop() -> None:
            asyncio.set_event_loop(loop)
            loop.run_forever()

        thread = threading.Thread(target=_run_loop, daemon=True, name="linear-official-mcp")
        thread.start()

        self._loop = loop
        self._thread = thread

    def _submit(self, coro: Any) -> Any:
        if not self._loop:
            raise RuntimeError("event loop not initialized")
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result(timeout=self._read_timeout_seconds + 10)

    async def _connect_async(self) -> None:
        if self._session is not None:
            return

        self._transport_cm = streamablehttp_client(
            self._url,
            headers=self._headers,
            timeout=self._timeout_seconds,
            sse_read_timeout=self._sse_read_timeout_seconds,
            terminate_on_close=False,
        )
        read_stream, write_stream, _ = await self._transport_cm.__aenter__()

        self._session_cm = ClientSession(
            read_stream,
            write_stream,
            read_timeout_seconds=timedelta(seconds=self._read_timeout_seconds),
        )
        self._session = await self._session_cm.__aenter__()
        await self._session.initialize()
        self._last_connected_at = time.time()

    async def _disconnect_async(self) -> None:
        if self._session_cm is not None:
            try:
                await self._session_cm.__aexit__(None, None, None)
            except Exception:
                pass
        if self._transport_cm is not None:
            try:
                await self._transport_cm.__aexit__(None, None, None)
            except Exception:
                pass

        self._session = None
        self._session_cm = None
        self._transport_cm = None

    def _ensure_connected(self) -> None:
        self._ensure_loop()
        self._submit(self._connect_async())

    def _normalize_result(self, result: Any) -> Any:
        if getattr(result, "isError", False):
            text = self._extract_text(result)
            raise OfficialToolError(
                "official_tool_error", text or "official MCP returned an error"
            )

        structured = getattr(result, "structuredContent", None)
        if structured is not None:
            return structured

        text = self._extract_text(result)
        if text:
            try:
                return json.loads(text)
            except Exception:
                return {"text": text}

        if hasattr(result, "model_dump"):
            return result.model_dump()
        return result

    @staticmethod
    def _extract_text(result: Any) -> str:
        content = getattr(result, "content", None) or []
        texts: list[str] = []
        for block in content:
            if getattr(block, "type", None) == "text":
                text = getattr(block, "text", "")
                if text:
                    texts.append(text)
        return "\n".join(texts).strip()

    def _record_failure(self, exc: Exception) -> None:
        self._failure_count += 1
        self._last_error = str(exc)
        logger.warning("Official MCP call failed: %s", exc)

    def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> Any:
        args = arguments or {}
        with self._lock:
            for attempt in range(2):
                try:
                    self._ensure_connected()
                    if self._session is None:
                        raise RuntimeError("official MCP session unavailable")
                    result = self._submit(self._session.call_tool(name, arguments=args))
                    self._failure_count = 0
                    self._last_error = None
                    return self._normalize_result(result)
                except Exception as exc:
                    self._record_failure(exc)
                    try:
                        self._submit(self._disconnect_async())
                    except Exception:
                        pass
                    if attempt == 1:
                        raise OfficialToolError(
                            "official_unavailable",
                            f"official MCP call failed for tool '{name}': {exc}",
                        ) from exc

        raise OfficialToolError("official_unavailable", "official MCP unavailable")

    def list_tools(self) -> list[str]:
        with self._lock:
            self._ensure_connected()
            if self._session is None:
                return []
            result = self._submit(self._session.list_tools())
            tools = getattr(result, "tools", []) or []
            return [t.name for t in tools if getattr(t, "name", None)]

    def get_health(self) -> dict[str, Any]:
        with self._lock:
            return {
                "url": self._url,
                "connected": self._session is not None,
                "failureCount": self._failure_count,
                "lastError": self._last_error,
                "lastConnectedAt": self._last_connected_at,
            }

    def close(self) -> None:
        with self._lock:
            if self._loop:
                try:
                    self._submit(self._disconnect_async())
                except Exception:
                    pass

                self._loop.call_soon_threadsafe(self._loop.stop)

            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=1.0)

            self._session = None
            self._session_cm = None
            self._transport_cm = None
            self._loop = None
            self._thread = None
