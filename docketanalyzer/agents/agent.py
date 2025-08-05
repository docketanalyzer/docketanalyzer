import os
from typing import Any

import simplejson as json

from docketanalyzer import env

from .tool import Tool


def export_env():
    """Export llm env for litellm."""
    keys = [
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
        "GEMINI_API_KEY",
        "COHERE_API_KEY",
        "GROQ_API_KEY",
    ]
    for key in keys:
        if key not in os.environ and env[key]:
            os.environ[key] = env[key]


class Agent:
    """Simplified litellm wrapper for chat models with tools."""

    default_model = "gpt-4.1-mini"
    default_completion_args = None
    default_tools = None

    def __init__(
        self,
        model: str | None = None,
        tools: list[Tool] | None = None,
        messages: list[dict[str, str]] | None = None,
        state: dict | None = None,
        max_steps: int = 30,
        temperature: float = 1e-16,
        **completion_args: dict[str, Any],
    ):
        """Init agent."""
        export_env()
        model = model or self.default_model
        args = {"model": model, "temperature": temperature, **completion_args}
        default_completion_args = self.default_completion_args or {}
        self.args = {**default_completion_args, **args}
        self.tools = tools or self.default_tools or []
        self.tools = {tool.__name__: tool for tool in self.tools}
        self.tool_schemas = [tool.get_schema() for tool in self.tools.values()]
        self.messages = messages or []
        self.state = state or {}
        self.r = None
        self.max_steps = max_steps

    @property
    def sanitized_messages(self):
        """Sanitize messages for display."""
        sanitized_messages = []
        for message in self.messages:
            sanitized_message = {"role": message["role"], "content": message["content"]}
            if "tool_calls" in message:
                sanitized_message["tool_calls"] = message["tool_calls"]
            if message["role"] == "tool":
                sanitized_message["tool_call_id"] = message["tool_call_id"]
            sanitized_messages.append(sanitized_message)
        return sanitized_messages

    def prepare_generation(
        self,
        messages: list[dict[str, str]] | str | None = None,
        tools: list[Tool | dict] | None = None,
        **completion_args: dict,
    ) -> dict:
        """Prepare arguments for generation."""
        if messages is not None:
            if isinstance(messages, str):
                messages = [{"role": "user", "content": messages}]
            self.messages.extend(messages)
        tool_schemas = self.tool_schemas
        if tools is not None:
            tool_schemas = []
            for tool in tools:
                if isinstance(tool, Tool):
                    self.tools[tool.__name__] = tool
                    tool_schemas.append(tool.get_schema())
                else:
                    tool_name = tool["function"]["name"]
                    if tool_name not in self.tools:
                        raise Exception(
                            f"'{tool_name}' is not defined. You must either pass "
                            "the Tool object or a schema matching a Tool the agent "
                            "was initialized with."
                        )
                    tool_schemas.append(tool)
        completion_args["tools"] = tool_schemas
        args = {**self.args, **completion_args}
        args["messages"] = self.sanitized_messages
        return args

    def step(
        self,
        messages: list[dict[str, str]] | str | None = None,
        tools: list[Tool | dict] | None = None,
        **completion_args: dict,
    ):
        """Take a single conversation step."""
        from litellm import completion

        args = self.prepare_generation(messages, tools, **completion_args)
        self.r = completion(**args)
        message = dict(self.r.choices[0].message)
        if message.get("tool_calls"):
            message["tool_calls"] = [
                dict(tool_call, function=dict(tool_call.function))
                for tool_call in message["tool_calls"]
            ]
        self.messages.append(message)
        finish_reason = self.r.choices[0].finish_reason
        return message, finish_reason

    def chat(
        self,
        messages: list[dict[str, str]] | str | None = None,
        **completion_args: dict,
    ) -> str:
        """Simple one step chat with no tools."""
        message, _ = self.step(messages, tools=[], **completion_args)
        return message["content"]

    def run(
        self,
        messages: list[dict[str, str]] | str | None = None,
        tools: list[Tool | dict] | None = None,
        **completion_args: dict,
    ):
        """Run a sequence of steps including tool calls."""
        message, finish_reason = self.step(messages, tools, **completion_args)
        steps = 1
        response_messages = [message]
        while steps < self.max_steps and finish_reason == "tool_calls":
            steps += 1
            tool_calls = self.messages[-1]["tool_calls"]
            for tool_call in tool_calls:
                tool_name = tool_call["function"]["name"]
                tool = self.tools[tool_name]
                tool_args = json.loads(tool_call["function"]["arguments"])
                tool_response = tool(**tool_args)(self)
                tool_data = {}
                if isinstance(tool_response, tuple):
                    tool_response, tool_data = tool_response
                self.messages.append(
                    {
                        "tool_call_id": tool_call["id"],
                        "role": "tool",
                        "content": tool_response,
                        "name": tool_name,
                        "data": tool_data,
                        "args": tool_args,
                    }
                )
            message, finish_reason = self.step(None, tools, **completion_args)
            response_messages.append(message)
        return response_messages

    async def stream(
        self,
        messages: list[dict[str, str]] | str | None = None,
        tools: list[Tool | dict] | None = None,
        **completion_args: dict,
    ):
        """Run a streaming generation with tool calls."""
        from litellm import acompletion

        steps, done = 0, False
        while steps < self.max_steps and not done:
            steps += 1

            args = self.prepare_generation(messages, tools, **completion_args)
            self.r = await acompletion(stream=True, **args)
            self.messages.append({"role": "assistant", "content": ""})
            tool_calls, messages = {}, None

            async for chunk in self.r:
                delta = chunk.choices[0].delta

                if delta.content:
                    if "tool_calls" in self.messages[-1]:
                        self.messages.append({"role": "assistant", "content": ""})
                    self.messages[-1]["content"] += delta.content
                    yield {"content_delta": delta.content}

                if delta.tool_calls:
                    if "tool_calls" not in self.messages[-1]:
                        self.messages.append(
                            {"role": "assistant", "content": "", "tool_calls": []}
                        )
                    for tool_call in delta.tool_calls:
                        if tool_call.index not in tool_calls:
                            tool_calls[tool_call.index] = {
                                "id": tool_call.id,
                                "type": tool_call.type,
                                "function": {
                                    "name": tool_call.function.name,
                                    "arguments": tool_call.function.arguments,
                                },
                            }
                        else:
                            if tool_call.function.arguments:
                                tool_calls[tool_call.index]["function"][
                                    "arguments"
                                ] += tool_call.function.arguments
                    self.messages[-1]["tool_calls"] = list(tool_calls.values())

                finish_reason = chunk.choices[0].finish_reason
                if finish_reason:
                    if finish_reason == "tool_calls":
                        yield self.messages[-1]
                        for tool_call in self.messages[-1].get("tool_calls", []):
                            tool_name = tool_call["function"]["name"]
                            tool = self.tools[tool_name]
                            tool_args = json.loads(tool_call["function"]["arguments"])
                            tool_response = await tool(**tool_args)(self)
                            tool_data = {}
                            if isinstance(tool_response, tuple):
                                tool_response, tool_data = tool_response
                            self.messages.append(
                                {
                                    "tool_call_id": tool_call["id"],
                                    "role": "tool",
                                    "name": tool_name,
                                    "content": tool_response,
                                    "data": tool_data,
                                    "args": tool_args,
                                }
                            )
                            yield self.messages[-1]
                    else:
                        done = True
