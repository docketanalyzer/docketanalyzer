from .label import Label


class EntryTypeLabel(Label):
    label_group = 'entry-type'


class AnswerLabel(EntryTypeLabel):
    name = 'answer'
    minimal_keywords_any = ['answer']


class ComplaintLabel(EntryTypeLabel):
    name = 'complaint'
    minimal_keywords_any = ['complaint']


class MotionLabel(EntryTypeLabel):
    name = 'motion'
    minimal_keywords_any = ['motion', 'petition']


class NoticeLabel(EntryTypeLabel):
    name = 'notice'
    minimal_keywords_any = ['notice']


class StipulationLabel(EntryTypeLabel):
    name = 'stipulation'
    minimal_keywords_any = ['stipulat']


class OrderLabel(EntryTypeLabel):
    name = 'order'
    minimal_keywords_any = ['order']


class MinuteEntryLabel(EntryTypeLabel):
    name = 'minute entry'
    minimal_keywords_any = ['minut']


class JudgmentLabel(EntryTypeLabel):
    name = 'judgment'
    minimal_keywords_any = ['judgment', 'judgement']


class DefaultJudgmentLabel(EntryTypeLabel):
    name = 'default judgment'
    minimal_keywords_any = ['default']
    training_args = {
        'num_train_epochs': 5,
        'per_device_train_batch_size': 16,
        'per_device_eval_batch_size': 16,
        'gradient_accumulation_steps': 1,
        'learning_rate': 5e-5,
        'weight_decay': 0.1,
        'warmup_ratio': 0.02,
        'evaluation_strategy': 'steps',
        'eval_steps': 0.08,
        'save_steps': 0.08,
        'save_total_limit': 2,
        'fp16': True,
    }
