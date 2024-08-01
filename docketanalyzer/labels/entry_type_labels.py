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
