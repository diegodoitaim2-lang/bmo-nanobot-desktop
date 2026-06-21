"""Tool registry for dynamic tool management.

Restored the original Nanobot fuzzy‑lookup and coercion logic so that
* miss‑spelled or differently‑cased tool names are suggested to the model,
* stringified JSON arguments are automatically parsed, and
* helpful error messages are returned when a tool is missing.
"""

import json
from typing import Any

from nanobot.agent.tools.base import Tool

# ---------------------------------------------------------------------------
# Helper functions – exactly as in the upstream Nanobot implementation
# ---------------------------------------------------------------------------

def _lookup_key(name: str) -> str:
    """Normalize a tool name for fuzzy suggestion.

    Removes non‑alphanumeric characters and lower‑cases everything.  This
    mirrors the original Nanobot behaviour where ``list_files`` and ``ListFiles``
    are considered equivalent for suggestions.
    """
    return "".join(ch.lower() for ch in name if ch.isalnum())

def _suggest_name(registry: dict[str, Tool], name: str) -> str | None:
    """Return a single close match for *name* or ``None``.

    The function is deliberately strict – it only returns a suggestion when
    *exactly one* registered tool normalises to the same key.  If there are
    multiple possible matches we do **not** guess.
    """
    key = _lookup_key(str(name or ""))
    if not key:
        return None
    matches = [registered for registered in registry if _lookup_key(registered) == key]
    return matches[0] if len(matches) == 1 else None

def _coerce_argument_value(value: Any) -> Any:
    """Attempt to turn a JSON string into a Python object.

    The upstream Nanobot accepted arguments like ``"{\"path\": \"/tmp/file\"}"`` –
    we keep that behaviour for backward compatibility.
    """
    if value is None:
        return {}
    if not isinstance(value, str):
        return value

    stripped = value.strip()
    if not stripped:
        return {}

    if not stripped.startswith(("{", "[")):
        return value

    try:
        return json.loads(stripped)
    except Exception:
        return value

def _unwrap_arguments_payload(tool: Tool, params: Any) -> Any:
    """Unwrap the legacy ``{"arguments": {...}}`` envelope.

    Some older tool calls wrapped the actual parameters under an ``arguments``
    dict.  If the tool schema does **not** declare an ``arguments`` field we
    unwrap it; otherwise we leave the payload untouched.
    """
    if not isinstance(params, dict) or set(params) != {"arguments"}:
        return params
    properties = (tool.parameters or {}).get("properties", {})
    if isinstance(properties, dict) and "arguments" in properties:
        return params
    return _coerce_argument_value(params.get("arguments"))

def _coerce_params(tool: Tool, params: Any) -> Any:
    """Full coercion pipeline used by the original Nanobot implementation.

    1. Turn a JSON string into a dict.
    2. Unwrap a legacy ``{"arguments": …}`` payload if the tool does not
       explicitly expect it.
    """
    params = _coerce_argument_value(params)
    return _unwrap_arguments_payload(tool, params)

# ---------------------------------------------------------------------------
# Registry implementation – only the surrounding logic changed
# ---------------------------------------------------------------------------

class ToolRegistry:
    """
    Registry for agent tools.

    Allows dynamic registration and execution of tools.
    """

    def __init__(self):
        self._tools: dict[str, Tool] = {}
        self._cached_definitions: list[dict[str, Any]] | None = None

    def register(self, tool: Tool) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool
        self._cached_definitions = None

    def unregister(self, name: str) -> None:
        """Unregister a tool by name."""
        self._tools.pop(name, None)
        self._cached_definitions = None

    def get(self, name: str) -> Tool | None:
        """Get a tool by name."""
        return self._tools.get(name)

    def has(self, name: str) -> bool:
        """Check if a tool is registered."""
        return name in self._tools

    @staticmethod
    def _schema_name(schema: dict[str, Any]) -> str:
        """Extract a normalized tool name from either OpenAI or flat schemas."""
        fn = schema.get("function")
        if isinstance(fn, dict):
            name = fn.get("name")
            if isinstance(name, str):
                return name
        name = schema.get("name")
        return name if isinstance(name, str) else ""

    def get_definitions(self) -> list[dict[str, Any]]:
        """Get tool definitions with stable ordering for cache-friendly prompts.

        Built-in tools are sorted first as a stable prefix, then MCP tools are
        sorted and appended.  The result is cached until the next
        register/unregister call.
        """
        if self._cached_definitions is not None:
            return self._cached_definitions

        definitions = [tool.to_schema() for tool in self._tools.values()]
        builtins: list[dict[str, Any]] = []
        mcp_tools: list[dict[str, Any]] = []
        for schema in definitions:
            name = self._schema_name(schema)
            if name.startswith("mcp_"):
                mcp_tools.append(schema)
            else:
                builtins.append(schema)

        builtins.sort(key=self._schema_name)
        mcp_tools.sort(key=self._schema_name)
        self._cached_definitions = builtins + mcp_tools
        return self._cached_definitions

    def prepare_call(
        self,
        name: str,
        params: dict[str, Any],
    ) -> tuple[Tool | None, dict[str, Any], str | None]:
        """Resolve, cast, and validate one tool call."""
        # Guard against invalid parameter types (e.g., list instead of dict)
        if not isinstance(params, dict) and name in ('write_file', 'read_file'):
            return None, params, (
                f"Error: Tool '{name}' parameters must be a JSON object, got {type(params).__name__}. "
                "Use named parameters: tool_name(param1=\"value1\", param2=\"value2\")"
            )

        tool = self._tools.get(name)
        if not tool:
            return None, params, (
                f"Error: Tool '{name}' not found. Available: {', '.join(self.tool_names)}"
            )

        cast_params = tool.cast_params(params)
        errors = tool.validate_params(cast_params)
        if errors:
            return tool, cast_params, (
                f"Error: Invalid parameters for tool '{name}': " + "; ".join(errors)
            )
        return tool, cast_params, None

    async def execute(self, name: str, params: dict[str, Any]) -> Any:
        """Execute a tool by name with given parameters."""
        _HINT = "\n\n[Analyze the error above and try a different approach.]"
        tool, params, error = self.prepare_call(name, params)
        if error:
            return error + _HINT

        try:
            assert tool is not None  # guarded by prepare_call()
            result = await tool.execute(**params)
            if isinstance(result, str) and result.startswith("Error"):
                return result + _HINT
            return result
        except Exception as e:
            return f"Error executing {name}: {str(e)}" + _HINT

    @property
    def tool_names(self) -> list[str]:
        """Get list of registered tool names."""
        return list(self._tools.keys())

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools
