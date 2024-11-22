from copy import deepcopy
import inspect
import time
from pathlib import Path
from pydantic import BaseModel
import simplejson as json
from docketanalyzer import generate_hash


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
    has_demo = False

    def __init__(self, cache_dir=None, messages=[], **kwargs):
        super().__init__(**kwargs)
        if cache_dir is not None: 
            cache_dir = Path(cache_dir)
            cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir = cache_dir
        self.messages = messages
        self.streaming_message = None
        self.done = False
        self.pause = False
        self.cache = {}
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
        return [self.chat_model.get_tool_schema(x) for x in self.tools]
    
    @property
    def last_tool_call_message(self):
        for message in reversed(self.messages):
            if 'tool_calls' in message:
                return message

    @property
    def chat_model(self):
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

    def chat(self, text=None, role=None, **kwargs):
        self.done = False
        if role is not None:
            self.messages.append(dict(role=role, content=text))
            print(self.messages)
            return None
        if text is not None:
            self.messages.append(dict(role='user', content=text))
        args = {**self.chat_args, **kwargs}
        args['stream'] = True
        tools_schema = self.tool_schemas
        if tools_schema:
            args['tools'] = args.get('tools', tools_schema)

        cache_args = dict(messages=self.chat_messages, args=args, model_args=self.chat_model_args)
        cache_hash = generate_hash(cache_args)
        cache_path = None if not self.cache_dir else self.cache_dir / f'{cache_hash}.json'
        if cache_path is not None and cache_path.exists():
            new_message = json.loads(cache_path.read_text())['response']
            self.messages.append(new_message)
            for streaming_message in self.on_stream_finish(**kwargs):
                yield streaming_message
        else:
            r = self.chat_model(self.chat_messages, **args)
            for stream in r:
                if self.done:
                    break
                while self.pause:
                    time.sleep(0.1)
                if len(stream.messages):
                    self.streaming_message = stream.messages[0]
                if stream.stop_reason:
                    self.messages.append(stream.messages.pop(0))
                    self.messages[-1]['stop_reason'] = stream.stop_reason
                    if cache_path is not None:
                        cache_args['response'] = self.messages[-1]
                        cache_path.write_text(json.dumps(cache_args, indent=2))
                    for streaming_message in self.on_stream_finish(**kwargs):
                        yield streaming_message
                else:
                    yield self.streaming_message
    
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
                    self.on_tool_result()
            if not self.done:
                for streaming_message in self.chat(**kwargs):
                    yield streaming_message
        self.done = True

    def on_tool_call(self, tool_name, arguments, tool_output, user_output):
        pass

    def on_tool_result(self):
        pass

    def on_new_message(self):
        pass

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

    @classmethod
    def get_demo_path(cls):
        if cls.has_demo:
            file_path = inspect.getfile(cls)
            return Path(file_path)
    

if __name__ == '__main__':
    import gradio as gr

    agent = Agent()

    def chat_fn(text):
        for streaming_message in agent.chat(text):
            yield gr.Chatbot(agent.get_gradio_messages())

    with gr.Blocks() as demo:
        chatbot = gr.Chatbot(type="messages", height=600)
        msg_input = gr.Textbox(show_label=False, submit_btn=True)
        msg = gr.Textbox(visible=False, interactive=False)

        msg_input.submit(
            lambda x: ("", x), [msg_input], [msg_input, msg],
        ).then(chat_fn, [msg], [chatbot])

    demo.launch()


