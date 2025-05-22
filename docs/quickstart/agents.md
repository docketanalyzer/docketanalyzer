# Agents Quickstart

Agents combine a language model with custom tools.

## Basic Agent

```python
from docketanalyzer import Agent, Tool

class EchoTool(Tool):
    text: str
    def __call__(self, agent=None):
        return self.text

agent = Agent(tools=[EchoTool])
agent("Say hi then call the tool with text='hello'")
print(agent.messages[-1]["content"])
```

## Streaming

```python
async for chunk in agent.stream("How are you?"):
    print(chunk)
```

## Weather Tool Examples

### Level 1 – Base Agent

```python
from docketanalyzer import Agent, Tool

class WeatherTool(Tool):
    """Return a canned weather string for the given location."""
    location: str

    def __call__(self, agent=None):
        return f"The weather in {self.location} is 72 degrees Fahrenheit."

question = (
    "What's the weather in New York and San Francisco? "
    "First take a guess, then use your tool."
)

agent = Agent(tools=[WeatherTool])
agent(question)
print(agent.messages[-1]["content"])
```

### Level 2 – Custom `__init__`

```python
class WeatherAgent(Agent):
    def __init__(self):
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

agent = WeatherAgent()
async for chunk in agent.stream("What's the weather in New York and San Francisco?"):
    if "content_delta" in chunk:
        print(chunk["content_delta"], end="")
```

### Level 3 – Overriding `__call__`

```python
class ComplaintAgent(Agent):
    def __init__(self):
        self.setup(chat={"model": "gpt-4o-mini"})

    def __call__(self, text: str):
        prompt = (
            "Extract the numbered claims from this complaint as JSON:"\
            f"\n\n{text}"
        )
        self.run(prompt)
        return self.messages[-1]["content"]

text = "1. Plaintiff claims breach of contract ... 2. Plaintiff claims negligence ..."
agent = ComplaintAgent()
claims = agent(text)
print(claims)
```
