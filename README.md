# docketanalyzer

## Install
````
  >> git clone https://github.com/docketanalyzer/docketanalyzer.git
  >> pip install -r docketanalyzer/requirements.txt
````
<br>

## Docket Classification Pipeline

Assign up to 66 tags to docket entry description text.  

````
  from docketanalyzer.pipelines import pipeline
  nlp = pipeline('docket-classification')
  labels = nlp(docket_texts)
````

Try it out with a GPU in Colab:

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1mpdTcOam8NKqZXDtX99NqrXIfNBZsv7C?usp=sharing)


You can also find the model on the Huggingface ModelHub:

  [docketanalyzer/distilroberta-base-ddcl](https://huggingface.co/docketanalyzer/distilroberta-base-ddcl)

<br>

## Docket Language Model

This model can be used as a starting point for finetuning your own docket classification or NER tasks.  Based on a distilroberta-base, this model is trained on the masked language modeling task for 7 epochs across 5 million docket entry descriptions.

Find it on the Huggingface ModelHub:

  [docketanalyzer/distilroberta-base-ddlm](https://huggingface.co/docketanalyzer/distilroberta-base-ddlm)







