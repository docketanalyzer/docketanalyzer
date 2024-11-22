# docketanalyzer

## Setup

Install with pip. You can then run `da configure` to store API keys and other configuration options.

```
pip install docketanalyzer
da configure
```

## Agents

A minimal, highly-hackable framework for creating interactive agentic workflows.

### Quickstart: Create a Weather Agent in 30 lines

<details>
<summary>Show example</summary>

#### 1. Define some tools.


```python
from enum import Enum
from pydantic import Field
from docketanalyzer import Agent, BaseTool, notabs

class Unit(str, Enum):
    f = 'f'
    c = 'c'

class get_weather(BaseTool):
    """
    Determine the weather in a specified location.
    """
    location: str = Field(..., description="The location to get the weather for.")
    unit: Unit = Field(..., description="The unit of temperature: 'f' for Fahrenheit or 'c' for Celsius.")

    def __call__(self):
        tool_output = user_output = (
            f"## Tool Output\n\n```\nThe weather in {self.location} is currently 90 degrees {self.unit}.\n```"
            f"\n\nWe have exchanged {len(self.agent.messages)} messages."
        )
        return tool_output, user_output
```

#### 2. Create an agent with tools and instructions.


```python
class WeatherAgent(Agent):
    name = "weather-agent"
    tools = [get_weather]
    instructions = notabs("""
    Chat with the user about whatever. If they ask about the weather, use your neat weather tool!
    You are *really* excited about getting to use your weather tool.
    Even when talking about other stuff, subtly nudge the conversation towards the weather.
    Be subtle though! Don't let the user catch on. Make them think it was *their* idea to ask about the weather.
    """)
```

#### 3. Build a UI for your agent.


```python
import gradio as gr

agent = WeatherAgent()

def chat_fn(text):
    for streaming_message in agent(text):
        yield gr.Chatbot(agent.get_gradio_messages())

with gr.Blocks() as demo:
    chatbot = gr.Chatbot(type="messages")
    msg_input = gr.Textbox(show_label=False, submit_btn=True)
    msg = gr.Textbox(visible=False, interactive=False)

    msg_input.submit(
        lambda x: ("", x), [msg_input], [msg_input, msg],
    ).then(chat_fn, [msg], [chatbot])

demo.launch()
```

</details>


### Build a Document Summarization Agent with Working Memory

<details>
<summary>Show Example</summary>

In this example we create an agent with a self-managed working memory that it can update. This is useful for tasks where you want to update or truncate the agent's message history at each step to save on context tokens.

#### 1. Add some tools

The `WorkingMemoryMixin` comes with three tools for adding/editing/deleting items in working memory. So we will create one additional tool for the model to signal when it's ready to move on to the next page. The `next_page` tool will interrupt and end the chat stream before the model can respond with a message about the tools it just used (which are wasted tokens for a more automated workflow like this one).


```python
from tqdm import tqdm
from docketanalyzer import Agent, BaseTool, WorkingMemoryMixin, extract_pages, notabs, package_data

class next_page(BaseTool):
    """
    Move to the next page of the document. Always call this after your working memory updates.
    """

    def __call__(self):
        self.agent.done = True
        return 'Success', None
```

#### 2. Create an agent with working memory

To use the `WorkingMemoryMixin` effectively, you should update your `agent.messages` to include your working memory state in `agent.working_memory_text`.

For agents `__call__` is intended to be the main entrypoint for using an agent. By defauly `__call__` simply wraps `agent.chat`, however this should be overriden for more custom workflows.

We also include a few hooks you can override for adding event handlers `on_tool_call` and `on_new_message`.


```python
class DocumentAgent(Agent, WorkingMemoryMixin):
    name = 'doc_agent'
    tools = [next_page]
    instructions= notabs("""
    We are summarizing long documents. We will do this in two stages:
    - First you will iterate through the pages of the document building up a list of notes.
    - Then there will be a summarization stage where you will use your notes to produce a final output.

    We are currently on the first stage. You will only be able to see the current page and your working memory state.
    Use your tools to add, edit, and delete notes in your working memory.
    These notes should be long, informative, and useful for the summarization stage.
    At the same time, you should edit and delete these notes to keep them concise as they do contribute to your context window.
    Include references to specific page numbers and quotes from the original text where appropriate.
    Call tools as needed until you are ready to proceed to the next page.
    Do not respond with any messages to the user. Just use your tools.
    """)

    def __init__(self, pages_per_step=5):
        super().__init__() # always call super if you override __init__!
        self.pages_per_step = pages_per_step
        self.clear()

    def clear(self):
        super().clear() # same for agent.clear
        self.pages = []
        self.current_page = 0
        self.summary = None

    @property
    def working_memory_tokens(self):
        return len(self.chat_model.tokenize(self.working_memory_text))

    @property
    def state_message(self): # we will use this as the user message
        template = notabs("""
        # Current State

        <working_memory>
        {working_memory}
        </working_memory>

        Your working memory is currently using {working_memory_tokens}. 
        Try to keep this below 8000 tokens by consolidating these notes.

        <pages>
        {pages}
        </pages>

        We are currently viewing pages {start} to {end} of {total_pages}.
        """)
        pages_text = [x['text'] for x in self.pages[self.current_page:self.current_page + self.pages_per_step]]
        pages_text = '\n\n---\n\n'.join(pages_text)
        text = template.replace('{working_memory}', self.working_memory_text)
        text = text.replace('{working_memory_tokens}', str(self.working_memory_tokens))
        text = text.replace('{pages}', pages_text)
        text = text.replace('{start}', str(self.current_page + 1))
        text = text.replace('{end}', str(self.current_page + 5))
        text = text.replace('{total_pages}', str(len(self.pages)))
        return text

    def summarize(self): # A one-off chat to get the final summary
        print("generating final summary")
        notes = '\n'.join(['- ' + x for x in self.working_memory])
        prompt = notabs(f"""
        We are summarizing a long document. We have condensed the document into the following notes:

        {notes}

        Generate a narrative-driven summary about the document based on these notes.
        Go into as much detail as possible, and make sure to reference specific page numbers and quotes from the original text where available.
        Aim for a final summary between 2000 and 4000 tokens.
        """)
        self.summary = self.chat_model(prompt, **self.chat_args)
        return self.summary
    
    def __call__(self, pages): # Custom entrypoint for processing iteratively self.pages_per_step pages at a time
        self.clear()
        self.pages = pages
        for current_page in tqdm(list(range(0, len(self.pages), self.pages_per_step))):
            self.current_page = current_page
            self.messages = [] # at each step we reset the message history
            for streaming_message in self.chat(self.state_message):
                yield streaming_message
        self.summarize()
    
    def on_tool_call(self, tool_name, arguments, tool_output, user_output):
        print("Page:", self.current_page, "Working Memory Tokens:", self.working_memory_tokens, "> using tool:", tool_name, arguments)
    
    def on_new_message(self):
        print(self.messages[-1]['content'])
```

#### Run the agent

We will first extract the text from a pdf.


```python
pdf_path = package_data('example-complaint').path
pages = extract_pages(pdf_path)
len(pages)
```

Iterate through the agent's stream.


```python
agent = DocumentAgent()
for _ in agent(pages):
    pass
```

And now we can view the agent's final summary:


```python
from pprint import pprint

print(len(agent.chat_model.tokenize(agent.summary)), "tokens")
pprint(agent.summary)
```

</details>

## Chat

TODO

## Document OCR

We have a simple utility for OCR and extracting text from PDFs. This is mostly taken from Free Law Project's [Doctor](https://github.com/freelawproject/doctor). The main tweak is that ours preserves page breaks. 

You should install `tesseract` on your system to leverage OCR.


```python
from docketanalyzer import extract_pages, package_data

pdf_path = package_data('example-complaint').path
pages = extract_pages(pdf_path)

# pages = [
#   {'text': 'The first page text ...', 'page': 1, 'ocr_needed': True},
#   {'text': 'The second page text ...', 'page': 2, 'ocr_needed': False},
#   ...
#]
```

## Docket Manager

TODO

## ML Extensions

Use the following to make sure you have all the needed requirements for the ML extensions:

```
pip install 'docketanalyzer[ml]'
```

### Pipelines

TODO

### Training Routines

TODO

</details>


```python
!jupyter nbconvert --to markdown README.ipynb
```

    [NbConvertApp] Converting notebook README.ipynb to markdown
    [NbConvertApp] Writing 9365 bytes to README.md
    

