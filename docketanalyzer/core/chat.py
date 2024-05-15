from copy import deepcopy
from groq import Groq
import instructor
from openai import OpenAI
from pathlib import Path
import simplejson as json
import tiktoken
import uuid
from docketanalyzer.utils import (
    notabs,
    GROQ_API_KEY, GROQ_DEFAULT_CHAT_MODEL,
    OPENAI_API_KEY, OPENAI_ORG_ID,
    OPENAI_DEFAULT_CHAT_MODEL, OPENAI_DEFAULT_EMBEDDING_MODEL,
)


class Chat:
    def __init__(self, api_key=None, organization=OPENAI_ORG_ID, base_url=None, mode='openai'):
        self.mode = mode
        if api_key is None:
            if mode == 'openai':
                api_key = OPENAI_API_KEY
            elif mode == 'groq':
                api_key = GROQ_API_KEY
        self.api_key = api_key
        self.organization = organization

        if mode == 'openai':
            self.client = instructor.patch(OpenAI(
                base_url=base_url,
                api_key=self.api_key,
                organization=self.organization,
            ))
            self.default_model = OPENAI_DEFAULT_CHAT_MODEL
        elif mode == 'groq':
            self.client = instructor.from_groq(Groq(
                api_key=self.api_key,
            ), mode=instructor.Mode.JSON)
            self.default_model = GROQ_DEFAULT_CHAT_MODEL
        else:
            raise ValueError("Invalid mode. Must be one of: 'openai', 'groq'")
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
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, json.dumps(args, sort_keys=True, default=str)))

    def chat(
        self, messages, system=None, model=None,
        response_model=None, temperature=0.0000000001, seed=42,
        cache_dir=None, verbose=False, **kwargs
    ):
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
            'response_model': response_model,
            **kwargs
        }

        response = None
        cache_path = None
        if cache_dir is not None:
            cache_id = self.get_cache_id(args)
            cache_path = Path(cache_dir) / f"{cache_id}.json"
            if cache_path.exists():
                response = json.loads(cache_path.read_text())['response']

        if response is None:
            response = self.client.chat.completions.create(**args)
            if response_model is None:
                response = response.choices[0].message.content
            else:
                response = response.dict()
            if cache_path is not None:
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                cache_path.write_text(json.dumps({'response': response}, indent=2))

        if verbose:
            print(f"\nUSER: {messages[-1]['content']}\n\nASSISTANT: {response}\n")
        return response

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

    def __call__(self, *args, **kwargs):
        return self.chat(*args, **kwargs)


class ChatThread:
    def __init__(self, messages=[], model=None, chat_args={}, data={}, parent=None, **kwargs):
        self.messages = deepcopy(messages)
        self.model = model if model is not None else Chat(**kwargs)
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
        response = self.model(self.history, **kwargs)
        self.messages.append({'role': 'assistant', 'content': response})
        return response

    def branch(self):
        thread = ChatThread(
            model=self.model,
            chat_args=self.chat_args,
            parent=self,
            data=self.data
        )
        self.children.append(thread)
        return thread

    def copy(self):
        return ChatThread(
            messages=self.messages,
            model=self.model,
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
