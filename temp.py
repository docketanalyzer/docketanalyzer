import ast
import pandas as pd

data = pd.read_csv('train.csv')
data['spans'] = data['spans'].apply(ast.literal_eval)
data['label'] = data['text'].apply(lambda x: int('judgment' in x.lower()))
data['labels'] = data['text'].apply(lambda x: [x for x in ['judgment', 'count', 'sentence'] if x in x.lower()])  

data = data[['text', 'label']]
from docketanalyzer.ml import training_routine


routine = training_routine(
    'classification',
    run_name='count-extract',
    data_dir='outputs',
    base_model='answerdotai/ModernBERT-base',
    run_args=dict(max_length=512),
    training_args=dict(
        num_train_epochs=1,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        gradient_accumulation_steps=1,
        bf16=True,
        save_steps=0.2,
        eval_steps=0.2,
        eval_strategy='steps',
        save_total_limit = 2,
        load_best_model_at_end = True,
        report_to='tensorboard',
        logging_dir='outputs/logs',
        logging_steps=1,
        overwrite_output_dir=True,
    )
)


routine.train(train_data=data.head(-100), eval_data=data.tail(100), overwrite=True)