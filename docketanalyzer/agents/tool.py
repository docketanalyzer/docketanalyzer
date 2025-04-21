from typing import Optional

import openai
from pydantic import BaseModel


class Tool(BaseModel):
    """A base class for tools that can be used by agents."""

    def __call__(
        self,
        agent: Optional["Agent"] = None,  # noqa: F821
    ) -> str | tuple[str, dict]:
        """Implement this method to define the tool's behavior.

        Args:
            agent: The agent instance that is calling this tool.

        Returns:
            A str tool response for the model. Or a tuple of str and a data dict.
        """
        raise NotImplementedError

    @classmethod
    def get_schema(cls):
        """Get the agent for this tool."""
        schema = openai.pydantic_function_tool(cls)
        schema["function"]["parameters"]["additionalProperties"] = False
        for params in schema["function"]["parameters"]["properties"].values():
            params.pop("default", None)
        return schema

    class Config:
        """Configuration to allow extra methods on the BaseModel."""

        extra = "allow"
