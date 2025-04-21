import asyncio
import logging

from docketanalyzer import env, notabs

from docketanalyzer import Chat


def test_anthropic():
    """Test Anthropic chat."""
    key_check = bool(env.ANTHROPIC_API_KEY)
    assert key_check, "ANTHROPIC_API_KEY is not set"

    chat = Chat(model="claude-3-5-haiku-latest")
    response = chat("Hi!")

    logging.info(f"Claude says: {response}")
    assert isinstance(response, str), "Response is not a string"
    assert len(response) > 0, "Response is empty"


def test_openai():
    """Test OpenAI chat."""
    key_check = bool(env.OPENAI_API_KEY)
    assert key_check, "OPENAI_API_KEY is not set"

    chat = Chat(model="openai/gpt-4o-mini")
    response = chat("Hi!")

    logging.info(f"GPT says: {response}")
    assert isinstance(response, str), "Response is not a string"
    assert len(response) > 0, "Response is empty"


def test_cohere():
    """Test Cohere chat."""
    key_check = bool(env.COHERE_API_KEY)
    assert key_check, "COHERE_API_KEY is not set"

    chat = Chat(model="command-light")
    response = chat("Hi!")

    logging.info(f"Command says: {response}")
    assert isinstance(response, str), "Response is not a string"
    assert len(response) > 0, "Response is empty"


def test_groq():
    """Test Groq chat."""
    key_check = bool(env.GROQ_API_KEY)
    assert key_check, "GROQ_API_KEY is not set"

    chat = Chat(model="groq/llama3-8b-8192")
    response = chat("Hi!")

    logging.info(f"Command says: {response}")
    assert isinstance(response, str), "Response is not a string"
    assert len(response) > 0, "Response is empty"


def test_together():
    """Test TogetherAI chat."""
    key_check = bool(env.TOGETHER_API_KEY)
    assert key_check, "TOGETHER_API_KEY is not set"

    chat = Chat(model="together_ai/meta-llama/Llama-3.2-3B-Instruct-Turbo")
    response = chat("Hi!")

    logging.info(f"Command says: {response}")
    assert isinstance(response, str), "Response is not a string"
    assert len(response) > 0, "Response is empty"


def test_chat_thread():
    """Test Chat with conversation history."""
    chat = Chat()
    chat(
        notabs("""
        This is a unit test to make sure we're maintaining conversation history.
        The secret number is 72.
                           
        Just respond with the word 'ok' and nothing else.
    """)
    )
    response = chat(
        notabs("""
        Ok, what was the secret number?
        Please respond with the number itself and nothing else.
    """),
        thread=True,
    )

    assert "72" in response, "Secret number not found in response"


def test_chat_stream():
    """Test Chat with conversation history."""
    chat = Chat()
    count = 0

    async def run_stream():
        nonlocal count
        async for _ in chat.stream("Write a beautiful sentence."):
            count += 1

    asyncio.run(run_stream())

    logging.info(chat.messages[-1]["content"])
    assert count > 5, "Too short a response"
    assert len(chat.messages) == 2, "Message not added to history"
