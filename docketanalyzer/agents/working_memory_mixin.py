from .agent import Agent, BaseTool


class add_working_memory_item(BaseTool):
    """
    Add or modify an item in the working memory.

    Args:
        content: The text for the new working memory item.
    """
    content: str

    def __call__(self):
        self.agent.working_memory.append(self.content)
        return 'Success', None


class edit_working_memory_item(BaseTool):
    """
    Modify an item in the working memory.

    Args:
        item_id: The id of the item to modify. See the <item> tags.
        content: The text to add to the working memory.
    """
    item_id: int
    content: str

    def __call__(self):
        if self.item_id is None:
            self.agent.working_memory.append(self.content)
            output = f"Added {self.content} to working memory."
        else:
            try:
                self.agent.working_memory[self.item_id] = self.content
            except IndexError:
                return "Item not found in working memory.", None
        return 'Success', None


class delete_working_memory_item(BaseTool):
    """
    Delete an item from the working memory.

    Args:
        item_id: The id of the item to delete. See the <item> tags.
    """
    item_id: int

    def __call__(self):
        try:
            self.agent.working_memory[self.item_id] = None
        except IndexError:
            return "Item not found in working memory.", None
        return 'Success', None


class WorkingMemoryMixin:
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.working_memory = []
        tools = [add_working_memory_item, edit_working_memory_item, delete_working_memory_item]
        for tool in tools:
            tool.set_agent(self)
        self.tools += tools

    def clear(self):
        super().clear()
        self.working_memory = []
    
    @property
    def working_memory_text(self):
        self.working_memory = [x for x in self.working_memory if x is not None]
        if not self.working_memory:
            return "Nothing here yet. You should add items here to maintain a sense of continuity as you proceed."
        items = [f"<item {i}> {x}" for i, x in enumerate(self.working_memory)]
        return '\n-----\n'.join(items)
    
    @property
    def working_memory_gradio(self):
        self.working_memory = [x for x in self.working_memory if x is not None]
        return '\n'.join(["- " + x for x in self.working_memory])
