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
