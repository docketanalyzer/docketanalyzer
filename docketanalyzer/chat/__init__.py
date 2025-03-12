from litellm import completion


class Chat:
    """
    Simplified litellm wrapper for chat models.
    
    Adds support for conversation history and message formatting.

    Attributes:
        args (dict): Arguments for the completion function.
        history (list): Conversation history.
        r: Response object from the completion function.
    """
    
    def __init__(self, model: str = "openai/gpt-4o-mini", temperature: float = 1e-16, **kwargs):
        """
        Load a Chat model.
        
        Args:
            model (str): The model identifier to use for completions.
                Default is "openai/gpt-4o-mini".
            temperature (float): Controls randomness in the model's responses.
                Lower values make responses more deterministic.
                Default is nearly 0 (very deterministic).
            **kwargs: Additional arguments to pass to the completion function.
        """
        self.args = {
            "model": model,
            "temperature": temperature,
            **kwargs
        }
        self.history = []
        self.r = None

    def __call__(self, messages: list[dict[str, str]] | str, thread: bool = False, **kwargs):
        """
        Generate a chat completion.
        
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
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]
        if not thread:
            self.history = []
        self.history.extend(messages)
        self.r = completion(
            messages=self.history,
            **self.args,
            **kwargs
        )
        return self.r.choices[0].message.content
