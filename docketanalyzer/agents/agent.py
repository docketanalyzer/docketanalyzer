import simplejson as json

from .chat import Chat
from .tool import Tool


class Agent:
    """A base class for agents that can use tools."""

    def __init__(
        self,
        messages: list[dict[str, str]] | None = None,
        tools: list[Tool] | None = None,
        chat: Chat | dict[str, str] | None = None,
        max_steps_per_run: int = 30,
        max_steps_per_lifetime: int = 100,
    ):
        """Initialize the agent.

        This method is intended to be overridden for custom agents.
            Use this space to setup any agent state attributes or configuration.
            You must call self.setup() in this method.
            You can use setup to add a fixed message history / system prompt,
            a fixed set of tools, or a custom chat model.
        """
        self.setup(
            messages=messages,
            tools=tools,
            chat=chat,
            max_steps_per_run=max_steps_per_run,
            max_steps_per_lifetime=max_steps_per_lifetime,
        )

    def __call__(self, messages: list[dict[str, str]] | str | None = None, **kwargs):
        """Main entry point for the agent.

        Intended to be overridden for custom workflows.
        """
        self.run(messages, **kwargs)

    def setup(
        self,
        messages: list[dict[str, str]] | None = None,
        tools: list[Tool] | None = None,
        chat: Chat | dict[str, str] | None = None,
        max_steps_per_run: int = 30,
        max_steps_per_lifetime: int = 100,
    ):
        """Setup basic agent config.

        This method should be called by the __init__ method of the agent.

        Args:
            messages: A list of message dictionaries to initialize the agent with.
                This is where you can add a system prompt or initial message history.
            tools: A list of tool classes to initialize the agent with.
            chat: A Chat instance or a dictionary to initialize the agent with.
            max_steps_per_run: The maximum number of steps the agent can run in a
                single call.
            max_steps_per_lifetime: The maximum number of steps the agent can run
                in its lifetime.

        """
        self.messages = messages or []
        self.tools = tools or []
        self.tools = {tool.__name__: tool for tool in self.tools}
        self.tool_schemas = [tool.get_schema() for tool in self.tools.values()]
        self.tool_call_data = {}
        if isinstance(chat, dict):
            chat = Chat(**chat)
        self.chat = chat or Chat()
        self.max_steps_per_run = max_steps_per_run
        self.max_steps_per_lifetime = max_steps_per_lifetime
        self.lifetime_steps = 0
        self.initialized = True

    def call_tools(self, tool_calls: list[dict[str, str]]) -> list[dict[str, str]]:
        """Call the tools with the given tool calls.

        This method runs the tool calls and adds the results to the message history.
        If your tool also returns a data dictionary, it is stored in the tool_call_data
        with the tool call id as the key.

        Args:
            tool_calls: A list of tool call dictionaries.
        """
        for tool_call in tool_calls:
            tool_name = tool_call["function"]["name"]
            tool = self.tools[tool_name]
            tool_args = json.loads(tool_call["function"]["arguments"])
            tool_response = tool(**tool_args)(self)
            tool_data = {}
            if isinstance(tool_response, tuple):
                tool_response, tool_data = tool_response
            self.tool_call_data[tool_call["id"]] = tool_data
            self.messages.append(
                {
                    "tool_call_id": tool_call["id"],
                    "role": "tool",
                    "name": tool_name,
                    "content": tool_response,
                }
            )

    def prepare_step(self, messages: list[dict[str, str]] | str | None = None):
        """Prepare the agent for a step."""
        if not hasattr(self, "initialized") or not self.initialized:
            raise ValueError("Agent not initialized. Your __init__ must call setup().")
        if self.lifetime_steps >= self.max_steps_per_lifetime:
            raise ValueError("Agent has reached max_steps_per_lifetime.")
        self.lifetime_steps += 1
        if messages is not None:
            if isinstance(messages, str):
                messages = [{"role": "user", "content": messages}]
            self.messages.extend(messages)

    def step(self, messages: list[dict[str, str]] | str | None = None, **kwargs) -> str:
        """Run a single step of the conversation."""
        self.prepare_step(messages)
        self.chat(messages=self.messages, tools=self.tool_schemas, **kwargs)
        self.messages = self.chat.messages
        if self.chat.finish_reason == "tool_calls":
            self.call_tools(self.messages[-1]["tool_calls"])

    def run(
        self,
        messages: list[dict[str, str]] | str,
        max_steps: int | None = None,
        **kwargs,
    ):
        """Run the agent with the given messages."""
        self.step(messages, **kwargs)
        max_steps = max_steps or self.max_steps_per_run
        num_steps = 1
        while self.chat.finish_reason == "tool_calls":
            if num_steps > max_steps:
                raise ValueError("Agent has reached max_steps.")
            self.step(**kwargs)
            num_steps += 1

    async def stream_step(
        self, messages: list[dict[str, str]] | str | None = None, **kwargs
    ):
        """Run a single step of the conversation with streaming."""
        self.prepare_step(messages)
        async for chunk in self.chat.stream(
            messages=self.messages, tools=self.tool_schemas, **kwargs
        ):
            delta = chunk.choices[0].delta
            if delta.content:
                yield {"content_delta": delta.content}
            if self.chat.finish_reason:
                self.messages = self.chat.messages
                if "tool_calls" in self.messages[-1]:
                    tool_calls = self.messages[-1]["tool_calls"]
                    for tool_call in tool_calls:
                        yield {"tool_call": tool_call}
                    self.call_tools(tool_calls)
                    for tool_call in tool_calls:
                        tool_call_data = self.tool_call_data[tool_call["id"]]
                        yield {"tool_result": {**tool_call, "result": tool_call_data}}
                    break

    async def stream(
        self,
        messages: list[dict[str, str]] | str,
        max_steps: int | None = None,
        **kwargs,
    ):
        """Run the agent with the given messages."""
        max_steps = max_steps or self.max_steps_per_run
        num_steps = 1
        async for response in self.stream_step(messages, **kwargs):
            yield response
        while self.chat.finish_reason == "tool_calls":
            if num_steps > max_steps:
                raise ValueError("Agent has reached max_steps.")
            async for response in self.stream_step(**kwargs):
                yield response
            num_steps += 1
