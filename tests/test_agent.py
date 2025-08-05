import asyncio
import logging
from typing import ClassVar

from docketanalyzer import Agent, Tool, env, notabs


class WeatherTool(Tool):
    """A tool to get the weather for a given location."""

    location: str

    def __call__(self, agent=None):
        """Mock tool call."""
        return f"The weather in {self.location} is 72 degrees Fahrenheit."


class AsyncWeatherTool(WeatherTool):
    """A tool to get the weather for a given location."""

    async def __call__(self, agent=None):
        """Mock tool call."""
        return super().__call__(agent)


class WeatherAgent(Agent):
    """A custom Agent that uses the WeatherTool."""

    default_model = "gpt-4.1-nano"
    default_tools: ClassVar[list[Tool]] = [AsyncWeatherTool]


def test_anthropic_chat():
    """Test Anthropic simple chat."""
    key_check = bool(env.ANTHROPIC_API_KEY)
    assert key_check, "ANTHROPIC_API_KEY is not set"

    agent = Agent(model="claude-3-5-haiku-latest")
    response = agent.chat("Hi!")

    logging.info(f"Claude says: {response}")
    assert isinstance(response, str), "Response is not a string"
    assert len(response) > 0, "Response is empty"


def test_openai_chat():
    """Test OpenAI simple chat."""
    key_check = bool(env.OPENAI_API_KEY)
    assert key_check, "OPENAI_API_KEY is not set"

    agent = Agent(model="gpt-4.1-mini")
    response = agent.chat("Hi!")

    logging.info(f"GPT says: {response}")
    assert isinstance(response, str), "Response is not a string"
    assert len(response) > 0, "Response is empty"


def test_cohere_chat():
    """Test Cohere simple chat."""
    key_check = bool(env.COHERE_API_KEY)
    assert key_check, "COHERE_API_KEY is not set"

    agent = Agent(model="command-light")
    response = agent.chat("Hi!")

    logging.info(f"Command says: {response}")
    assert isinstance(response, str), "Response is not a string"
    assert len(response) > 0, "Response is empty"


def test_gemini_chat():
    """Test Gemini simple chat."""
    key_check = bool(env.GEMINI_API_KEY)
    assert key_check, "GEMINI_API_KEY is not set"

    agent = Agent(model="gemini/gemini-2.5-flash")
    response = agent.chat("Hi!")

    logging.info(f"Gemini says: {response}")
    assert isinstance(response, str), "Response is not a string"
    assert len(response) > 0, "Response is empty"


def test_groq_chat():
    """Test Groq simple chat."""
    key_check = bool(env.GROQ_API_KEY)
    assert key_check, "GROQ_API_KEY is not set"

    agent = Agent(model="groq/llama3-8b-8192")
    response = agent.chat("Hi!")

    logging.info(f"Command says: {response}")
    assert isinstance(response, str), "Response is not a string"
    assert len(response) > 0, "Response is empty"


def test_conversation_history():
    """Test persistent conversation history."""
    agent = Agent()
    agent.run(
        notabs("""
        This is a unit test to make sure we're maintaining conversation history.
        The secret number is 72.
                           
        Just respond with the word 'ok' and nothing else.
    """)
    )

    response_messages = agent.run(
        notabs("""
        Ok, what was the secret number?
        Please respond with the number itself and nothing else.
    """)
    )
    response = response_messages[-1]["content"]

    assert "72" in response, "Secret number not found in response"
    assert len(agent.messages) == 4, "Message history length not correct"


def test_agent_stream():
    """Test Agent streaming response."""
    agent = Agent()
    count = 0

    async def run_stream():
        nonlocal count
        async for chunk in agent.stream("Write a beautiful sentence."):
            assert "content_delta" in chunk, "No content delta in response"
            count += 1

    asyncio.run(run_stream())

    logging.info(agent.messages[-1]["content"])
    assert count > 5, "Too short a response"
    assert len(agent.messages) == 2, "Message history length not correct"


def test_agent_tool_use():
    """Test Agent with weather tool."""
    message = notabs("""
        What's the weather in New York and San Francisco? 
        First take a guess, then use your tool.
        Important: Respond to the user with your guess *before* you use your tool.
    """)
    agent = Agent(tools=[WeatherTool])
    agent.run(message)

    tool_calls = 0
    tool_results = 0
    user_messages = 0
    assistant_messages = 0
    for message in agent.messages:
        if message["role"] == "user":
            user_messages += 1
        elif message["role"] == "assistant":
            if message.get("content"):
                assistant_messages += 1
            for _ in message.get("tool_calls") or []:
                tool_calls += 1
        elif message["role"] == "tool":
            tool_results += 1

    last_response = agent.messages[-1]["content"]
    assert user_messages == 1, "Expected one user message"
    assert assistant_messages == 2, "Expected two assistant messages"
    assert tool_calls == 2, "Expected two tool call messages"
    assert tool_results == 2, "Expected two tool result messages"
    assert "72" in last_response, "Temperature not found in response"


def test_streaming_agent_tool_use():
    """Test customn Agent with stream."""
    message = "What's the weather in New York and San Francisco?"

    agent = WeatherAgent()

    content_delta_count = 0
    tool_calls = 0
    tool_results = 0

    async def run_stream():
        nonlocal content_delta_count, tool_calls, tool_results
        async for chunk in agent.stream(message):
            if "content_delta" in chunk:
                content_delta_count += 1
            for _ in chunk.get("tool_calls") or []:
                tool_calls += 1
            if "tool_call_id" in chunk:
                tool_results += 1

    asyncio.run(run_stream())

    last_response = agent.messages[-1]["content"]
    assert content_delta_count > 5, "Too few content deltas in response stream"
    assert tool_calls == 2, "Expected two tool calls in response stream"
    assert tool_results == 2, "Expected two tool results in response stream"
    assert "72" in last_response, "Temperature not found in response"
