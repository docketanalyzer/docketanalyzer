import os
from typing import Any

from .. import env


def export_env():
    """Export llm env for litellm."""
    keys = [
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
        "TOGETHER_API_KEY",
        "COHERE_API_KEY",
        "GROQ_API_KEY",
    ]
    for key in keys:
        if key not in os.environ and env[key]:
            os.environ[key] = env[key]


class Chat:
    """Simplified litellm wrapper for chat models.

    Adds support for conversation history and message formatting.

    Attributes:
        args (dict): Arguments for the completion function.
        messages (list): Conversation history.
        r: Response object from the completion function.
        streaming_message (dict | None): Current message being streamed.
        finish_reason (str | None): Reason for completion finish.
    """

    def __init__(
        self,
        model: str = "openai/gpt-4o-mini",
        temperature: float = 1e-16,
        **kwargs: dict[str, Any],
    ):
        """Load a Chat model.

        Args:
            model (str): The model identifier to use for completions.
                Default is "openai/gpt-4o-mini".
            temperature (float): Controls randomness in the model's responses.
                Lower values make responses more deterministic.
                Default is nearly 0 (very deterministic).
            **kwargs: Additional arguments to pass to the completion function.
        """
        export_env()
        self.args = {"model": model, "temperature": temperature, **kwargs}
        self.messages = []
        self.r = None
        self.streaming_message = None
        self.finish_reason = None

    def prepare_generation(
        self,
        messages: list[dict[str, str]] | str,
        thread: bool = False,
        **kwargs: dict[str, Any],
    ) -> dict:
        """Prepare arguments for the completion function."""
        self.finish_reason = None
        self.streaming_message = None
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]
        if not thread:
            self.messages = []
        self.messages.extend(messages)
        kwargs = {**self.args, **kwargs}
        kwargs["messages"] = self.messages
        return kwargs

    def __call__(
        self,
        messages: list[dict[str, str]] | str,
        thread: bool = False,
        **kwargs: dict[str, Any],
    ) -> str:
        """Generate a chat completion.

        Args:
            messages (list[dict[str, str]] | str): Either a string message or a list of
                message dictionaries with 'role' and 'content' keys.
                If a string is provided, it's converted to a user message.
            thread (bool): If True, maintains conversation history between calls.
                If False, conversation history is reset. Default is False.
            **kwargs: Additional arguments to pass to the completion function,
                which will override any arguments set during initialization.

        Returns:
            str: The content of the model's response message.
        """
        from litellm import completion

        args = self.prepare_generation(messages, thread=thread, **kwargs)
        self.r = completion(**args)
        message = dict(self.r.choices[0].message)
        if message.get("tool_calls"):
            message["tool_calls"] = [
                dict(tool_call, function=dict(tool_call.function))
                for tool_call in message["tool_calls"]
            ]
        self.messages.append(message)
        self.finish_reason = self.r.choices[0].finish_reason
        return message["content"]

    async def stream(
        self,
        messages: list[dict[str, str]] | str,
        thread: bool = False,
        **kwargs: dict[str, Any],
    ):
        """Generate a chat completion with async streaming.

        Args:
            messages (list[dict[str, str]] | str): Either a string message or a list of
                message dictionaries with 'role' and 'content' keys.
                If a string is provided, it's converted to a user message.
            thread (bool): If True, maintains conversation history between calls.
                If False, conversation history is reset. Default is False.
            **kwargs: Additional arguments to pass to the completion function,
                which will override any arguments set during initialization.

        Returns:
            ModelResponseStream: An async generator yielding response chunks.
                Each chunk a delta for the model's response.
        """
        from litellm import acompletion

        args = self.prepare_generation(messages, thread=thread, **kwargs)
        self.r = await acompletion(stream=True, **args)
        self.streaming_message = {"role": "assistant", "content": ""}
        tool_calls = {}
        async for chunk in self.r:
            delta = chunk.choices[0].delta
            # Update message content
            if delta.content:
                self.streaming_message["content"] += delta.content

            # Update tool calls
            if delta.tool_calls:
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
                            tool_calls[tool_call.index]["function"]["arguments"] += (
                                tool_call.function.arguments
                            )
                self.streaming_message["tool_calls"] = list(tool_calls.copy().values())

            # Set finish reason
            if chunk.choices[0].finish_reason:
                self.messages.append(self.streaming_message)
                self.streaming_message = None
                self.finish_reason = chunk.choices[0].finish_reason

            yield chunk
