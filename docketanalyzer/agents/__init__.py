from docketanalyzer import Registry
from .chat import Chat, ChatStream
from .agent import Agent, BaseTool
from .working_memory_mixin import WorkingMemoryMixin


class AgentRegistry(Registry):
    """
    A registry for agents.
    """
    def find_filter(self, obj):
        return isinstance(obj, type) and issubclass(obj, Agent) and obj.name is not None


agent_registry = AgentRegistry()
agent_registry.find()


def load_agent(name, **kwargs):
    for agent_class in agent_registry.all():
        if agent_class.name == name:
            return agent_class(**kwargs)
    raise ValueError(f'Agent "{name}" not found.')


def register_agent(agent_class):
    agent_registry.register(agent_class.__name__, agent_class)
