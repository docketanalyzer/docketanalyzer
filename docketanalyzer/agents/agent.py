from copy import deepcopy
import time
from pydantic import BaseModel
import simplejson as json
from docketanalyzer import notabs


class BaseTool(BaseModel):
    def __call__(self):
        raise NotImplementedError

    @classmethod
    def set_agent(cls, agent):
        cls.agent = agent
    
    class Config:
        extra = 'allow'


class Agent:
    name = None
    tools = []
    chat_model_args = dict(mode='openai', model='gpt-4o-mini')
    chat_args = dict()
    instructions = None

    def __init__(self, messages=[], cache_dir=None, **kwargs):
        super().__init__(**kwargs)
        self.tools = deepcopy(self.tools)
        self.instructions = deepcopy(self.instructions)
        self.messages = messages
        self.streaming_message = None
        self.done = False
        self.pause = False
        self.cache = {}
        if cache_dir is not None:
            self.chat_args['cache_dir'] = cache_dir
        for tool in self.tools:
            tool.set_agent(self)
    
    def clear(self):
        self.messages = []
        self.streaming_message = None
        self.done = False
        self.cache = {}
    
    @property
    def tool_classes(self):
        return {tool.__name__: tool for tool in self.tools}
    
    @property
    def tool_schemas(self):
        return [self.chat.get_tool_schema(x) for x in self.tools]
    
    @property
    def last_tool_call_message(self):
        for message in reversed(self.messages):
            if 'tool_calls' in message:
                return message

    @property
    def chat(self):
        from docketanalyzer import Chat
        return Chat(**self.chat_model_args)

    @property
    def chat_messages(self):
        messages = []
        if self.instructions:
            messages.append(dict(role='system', content=self.instructions))
        for message in self.messages:
            messages.append({k: message[k] for k in ['role', 'content', 'tool_calls', 'tool_call_id'] if k in message})
        return messages

    @property
    def streaming_messages(self):
        return self.messages + [self.streaming_message] if self.streaming_message else self.messages

    def step(self, text=None, role=None, **kwargs):
        self.done = False
        if role is not None:
            self.messages.append(dict(role=role, content=text))
            return
        if text is not None:
            self.messages.append(dict(role='user', content=text))
        args = {**self.chat_args, **kwargs}
        args['stream'] = True
        tools_schema = self.tool_schemas
        if tools_schema:
            args['tools'] = args.get('tools', tools_schema)

        stream = self.chat(self.chat_messages, **args)
        for _ in stream:
            if self.done or stream.stop_reason:
                break
            while self.pause:
                time.sleep(0.1)
            self.streaming_message = stream.response
            yield self.streaming_message
        response = stream.response
        response['stop_reason'] = stream.stop_reason
        self.streaming_message = None
        self.messages.append(response)
        for streaming_message in self.on_stream_finish(**kwargs):
            yield streaming_message
        yield deepcopy(response)
    
    def on_stream_finish(self, **kwargs):
        self.streaming_message = None
        self.on_new_message()
        if self.messages[-1]['stop_reason'] == 'tool_calls':
            for tool_call in self.messages[-1]['tool_calls']:
                function = tool_call['function']
                arguments = json.loads(function['arguments'])
                tool_output, user_output = self.tool_classes[function['name']](**arguments)()
                self.on_tool_call(function['name'], arguments, tool_output, user_output)
                if tool_output is not None:
                    self.messages.append(dict(
                        role='tool', content=tool_output, user_content=user_output, tool_call_id=tool_call['id']
                    ))
            if not self.done:
                for streaming_message in self.step(**kwargs):
                    yield streaming_message
        self.done = True

    def on_tool_call(self, tool_name, arguments, tool_output, user_output):
        pass

    def on_new_message(self):
        pass

    def __call__(self, *args, **kwargs):
        return self.step(*args, **kwargs)

    def get_gradio_messages(self, messages=None):
        if messages is None:
            messages = self.streaming_messages
        gradio_messages = []
        for message in deepcopy(messages):
            tool_calls = message.get('tool_calls', [])
            if tool_calls:
                content = []
                for tool_call in tool_calls:
                    function = tool_call['function']
                    args = function['arguments']
                    try:
                        args = json.dumps(json.loads(args), indent=2)
                    except:
                        pass
                    tool_template = notabs("""
                        <details>
                        <summary>USING TOOL: {name}</summary>

                        ```json
                        {args}
                        ```

                        </details>
                    """)
                    content.append(tool_template.format(name=function['name'], args=args))
                message['content'] = '\n\n\n\n'.join(content)
            if message['role'] == 'tool':
                message['role'] = 'assistant'
                message['content'] = message['user_content']
            if message.get('content') is not None:
                gradio_messages.append(message)
        return gradio_messages
