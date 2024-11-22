from copy import deepcopy
from anthropic import Anthropic
from cohere import Client as CohereClient
from groq import Groq
import openai
from openai import OpenAI
from pathlib import Path
import simplejson as json
import tiktoken
from docketanalyzer import (
    notabs, generate_hash,
    ANTHROPIC_API_KEY, ANTHROPIC_DEFAULT_CHAT_MODEL,
    GROQ_API_KEY, GROQ_DEFAULT_CHAT_MODEL,
    OPENAI_API_KEY, OPENAI_DEFAULT_CHAT_MODEL, OPENAI_DEFAULT_EMBEDDING_MODEL,
    COHERE_API_KEY, COHERE_DEFAULT_CHAT_MODEL,
    TOGETHER_API_KEY, TOGETHER_DEFAULT_CHAT_MODEL,
    RUNPOD_API_KEY,
)


class ChatStream:
    def __init__(self, stream, mode='openai'):
        self.stream = stream
        self.mode = mode
        self.messages = []
        self.stop_reason = None

    def __iter__(self):
        for chunk in self.stream:
            self.stop_reason = None
            if self.mode == 'anthropic':
                raise Exception("Need to finish this.")
                if chunk.type == 'message_delta' and chunk.delta.stop_reason:
                    self.stop_reason = chunk.delta.stop_reason
                if chunk.type == 'message_start':
                    self.messages.append({'role': chunk.message.role, 'content': ''})
                elif chunk.type == 'content_block_start' and chunk.content_block.type == 'tool_use':
                    self.messages.append({'role': 'tool', 'tool': chunk.content_block.name, 'arguments': '', 'tool_call_id': chunk.content_block.id})
                elif chunk.type == 'content_block_delta':
                    if chunk.delta.type == 'input_json_delta':
                        self.messages[-1]['arguments'] += chunk.delta.partial_json
                    else:
                        self.messages[-1]['content'] += chunk.delta.text
            else:
                choice = chunk.choices[0]
                self.stop_reason = choice.finish_reason
                if choice.delta.role:
                    self.messages.append({'role': choice.delta.role, 'content': ''})
                if choice.delta.content:
                    self.messages[-1]['content'] += choice.delta.content
                if choice.delta.tool_calls:
                    for tool_call in choice.delta.tool_calls:
                        function = tool_call.function
                        if function.name:
                            self.messages[-1]['tool_calls'] = self.messages[-1].get('tool_calls', [])
                            self.messages[-1]['tool_calls'].append({'id': tool_call.id, 'type': 'function', 'function': {'name': function.name, 'arguments': ''}})
                        if function.arguments:
                            self.messages[-1]['tool_calls'][-1]['function']['arguments'] += function.arguments
            yield self


class Chat:
    def __init__(self, api_key=None, base_url=None, mode='openai', model=None):
        self.mode = mode
        if api_key is None:
            if mode == 'anthropic':
                api_key = ANTHROPIC_API_KEY
            elif mode == 'openai':
                api_key = OPENAI_API_KEY
            elif mode == 'vllm':
                api_key = RUNPOD_API_KEY
            elif mode == 'groq':
                api_key = GROQ_API_KEY
            elif mode == 'cohere':
                api_key = COHERE_API_KEY
            elif mode == 'together':
                api_key = TOGETHER_API_KEY
        self.api_key = api_key

        if mode == 'anthropic':
            self.client = Anthropic(api_key=self.api_key)
            self.default_model = ANTHROPIC_DEFAULT_CHAT_MODEL

        elif mode in ['openai', 'vllm']:
            self.client = OpenAI(base_url=base_url, api_key=self.api_key)
            self.default_model = OPENAI_DEFAULT_CHAT_MODEL
        
        elif mode == 'groq':
            self.client = Groq(api_key=self.api_key)
            self.default_model = GROQ_DEFAULT_CHAT_MODEL

        elif mode == 'cohere':
            self.client = CohereClient(api_key=self.api_key)
            self.default_model = COHERE_DEFAULT_CHAT_MODEL

        elif mode == 'together':
            self.client = OpenAI(base_url='https://api.together.xyz/v1', api_key=self.api_key)
            self.default_model = TOGETHER_DEFAULT_CHAT_MODEL

        else:
            raise ValueError("Invalid mode. Must be one of: 'anthropic', 'cohere', 'groq', 'openai', 'together'")
        if model is not None:
            self.default_model = model
        self.r = None
        self.cache = {}

    def embed(self, texts, model=OPENAI_DEFAULT_EMBEDDING_MODEL):
        if self.mode != 'openai':
            raise ValueError("Embeddings are only supported by OpenAI.")
        texts = [x.replace("\n", " ") for x in texts]
        results = self.client.embeddings.create(input=texts, model=model).data
        return [x.embedding for x in results]

    def get_cache_id(self, args):
        args = deepcopy(args)
        args['mode'] = self.mode
        if args.get('response_model'):
            args['response_model'] = args['response_model'].schema()
        return str(generate_hash(args))

    def chat(
        self, messages, system=None, model=None,
        temperature=0.00000000000001, seed=42,
        cache_dir=None, verbose=False, stream=False, **kwargs
    ):
        if stream and cache_dir is not None:
            raise ValueError("Cannot use stream and cache_dir together.")
        if model is None:
            model = self.default_model
        if isinstance(messages, str):
            messages = [{'role': 'user', 'content': messages}]
        if system is not None:
            messages = [{'role': 'system', 'content': system}] + messages

        args = {
            'model': model,
            'messages': messages,
            'temperature': temperature,
            'seed': seed,
            'stream': stream,
            **kwargs
        }

        if self.mode == 'anthropic':
            args['max_tokens'] = args.get('max_tokens', 4000)
            del args['seed']


        response = None
        cache_path = None
        if cache_dir is not None:
            cache_id = self.get_cache_id(args)
            cache_path = Path(cache_dir) / f"{cache_id}.json"
            if cache_path.exists():
                response = json.loads(cache_path.read_text())['response']

        if response is None:
            if 'response_format' in kwargs and self.mode == 'openai':
                self.r = self.client.beta.chat.completions.parse(**args)
                response = self.r.choices[0].message.parsed.dict()
            else:
                if self.mode == 'anthropic':
                    self.r = self.client.messages.create(**args)
                else:
                    self.r = self.client.chat.completions.create(**args)
                
                if stream:
                    return ChatStream(self.r, mode=self.mode)

                if self.mode == 'anthropic':
                    response = self.r.content[0].text
                elif self.mode == 'cohere':
                    response = self.r.text
                else:
                    response = self.r.choices[0].message.content
            if cache_path is not None:
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                cache_path.write_text(json.dumps({'response': response}, indent=2))

        if verbose:
            print(f"\nUSER: {messages[-1]['content']}\n\nASSISTANT: {response}\n")
        return response

    def get_tool_schema(self, tool_class):
        schema = openai.pydantic_function_tool(tool_class)
        schema['function']['parameters']['additionalProperties'] = False
        for params in schema['function']['parameters']['properties'].values():
            params.pop('default', None)
        if self.mode == 'vllm':
            schema['function'].pop('strict')
        if self.mode == 'anthropic':
            schema = schema['function']
            return dict(name=schema['name'], description=schema['description'], input_schema = schema['parameters'])
        return schema

    def get_tokenizer(self, model):
        key = f'tokenizer__{model}'
        if self.cache.get(key) is None:
            self.cache[key] = tiktoken.encoding_for_model(model)
        return self.cache.get(key)

    def tokenize(self, text, model=None):
        model = model if model is not None else self.default_model
        tokenizer = self.get_tokenizer(model)
        return tokenizer.encode(text)

    def decode(self, tokens, model=None):
        model = model if model is not None else self.default_model
        tokenizer = self.get_tokenizer(model)
        return tokenizer.decode(tokens)

    def truncate(self, text, max_length, model=None):
        tokens = self.tokenize(text, model)
        tokens = tokens[:max_length]
        return self.decode(tokens, model)

    def __call__(self, *args, **kwargs):
        return self.chat(*args, **kwargs)


class ChatThread:
    def __init__(self, messages=[], chat_model=None, chat_args={}, data={}, parent=None, **kwargs):
        self.messages = deepcopy(messages)
        self.chat_model = chat_model if chat_model is not None else Chat(**kwargs)
        self.chat_args = chat_args
        self.data = data
        self.parent = parent
        self.children = []

    @property
    def history(self):
        history = self.messages
        if self.parent is not None:
            history = self.parent.history + history
        return history

    def __getitem__(self, key):
        return self.data.get(key)

    def __setitem__(self, key, value):
        self.data[key] = value

    def __call__(self, *args, **kwargs):
        return self.chat(*args, **kwargs)

    def chat(self, text, clean_text=True, role=None, **kwargs):
        if not isinstance(text, str):
            raise ValueError("Text must be a string.")
        if clean_text:
            text = notabs(text)
        if role is not None:
            self.messages.append({'role': role, 'content': text})
            return None
        self.messages.append({'role': 'user', 'content': text})
        for k, v in self.chat_args.items():
            if k not in kwargs:
                kwargs[k] = v
        response = self.chat_model(self.history, **kwargs)
        self.messages.append({'role': 'assistant', 'content': response})
        return response

    def branch(self):
        thread = ChatThread(
            chat_model=self.chat_model,
            chat_args=self.chat_args,
            parent=self,
            data=self.data
        )
        self.children.append(thread)
        return thread

    def copy(self):
        return ChatThread(
            messages=self.messages,
            chat_model=self.chat_model,
            chat_args=self.chat_args,
            data=deepcopy(self.data),
            parent=self.parent
        )

    @property
    def response(self):
        if len(self.messages) > 0:
            return self.messages[-1]['content']

    @property
    def response_yes_no(self):
        last_response = self.response
        if last_response:
            first_word = last_response.strip().split()[0].lower()
            if len(first_word) < 5:
                if first_word.startswith('yes'):
                    return True
                elif first_word.startswith('no'):
                    return False
        return None

    @property
    def response_json(self):
        last_response = self.response
        if last_response:
            try:
                return json.loads(last_response)
            except:
                return None
        return None
