import pandas as pd
from pipelines import pipeline

data = pd.read_csv('data/docket_text.csv')
docs = list(data['docket_text'].values)

nlp = pipeline('docket-classification')

data['labels'] = nlp(docs)
data.to_csv('data/tagged_docket_text.csv', index=False)
