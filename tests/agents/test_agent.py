import asyncio

from docketanalyzer import Agent, Tool, notabs


class WeatherTool(Tool):
    """A tool to get the weather for a given location."""

    location: str

    def __call__(self, agent=None):
        """Mock tool call."""
        return f"The weather in {self.location} is 72 degrees farenheit."


class WeatherAgent(Agent):
    """A custom Agent that uses the WeatherTool."""

    def __init__(self):
        """Initialize the agent with fixed system prompt and tools."""
        self.setup(
            messages=[
                {
                    "role": "system",
                    "content": "Always rhyme, and use your tool if asked about weather",
                }
            ],
            tools=[WeatherTool],
            chat={"model": "gpt-4o-mini"},
        )


def test_default_agent_run():
    """Test default Agent with tools passed to init using run."""
    message = notabs("""
        What's the weather in New York and San Francisco? 
        First take a guess, then use your tool.
    """)
    agent = Agent(tools=[WeatherTool])
    agent(message)

    tool_call_messages = 0
    tool_result_messages = 0
    user_messages = 0
    assistant_messages = 0
    for message in agent.messages:
        if message["role"] == "user":
            user_messages += 1
        elif message["role"] == "assistant":
            if message.get("tool_calls"):
                tool_call_messages += 1
            assistant_messages += 1
        elif message["role"] == "tool":
            tool_result_messages += 1

    assert user_messages == 1, "Expected one user message"
    assert assistant_messages == 2, "Expected two assistant messages"
    assert tool_call_messages == 1, "Expected one tool call message"
    assert tool_result_messages == 2, "Expected two tool result messages"


def test_custom_agent_stream():
    """Test customn Agent with stream."""
    message = "What's the weather in New York and San Francisco?"

    agent = WeatherAgent()

    content_delta_count = 0
    tool_call_counts = 0
    tool_result_counts = 0

    async def run_stream():
        nonlocal content_delta_count, tool_call_counts, tool_result_counts
        async for response in agent.stream(message):
            if "content_delta" in response:
                content_delta_count += 1
            if "tool_call" in response:
                tool_call_counts += 1
            if "tool_result" in response:
                tool_result_counts += 1

    asyncio.run(run_stream())

    assert content_delta_count > 5, "Too few content deltas in response stream"
    assert tool_call_counts == 2, "Expected two tool calls in response stream"
    assert tool_result_counts == 2, "Expected two tool results in response stream"
