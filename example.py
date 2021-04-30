import pandas as pd
from pipelines import pipeline

data = pd.read_csv('data/dockets.csv')
docs = list(data['docket_text'].values)

nlp = pipeline('docket-classification')

data['labels'] = nlp(docs)
data.to_csv('data/tagged_dockets.csv', index=False)
