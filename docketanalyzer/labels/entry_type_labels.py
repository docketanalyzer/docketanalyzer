from .label import Label


class EntryTypeLabel(Label):
    label_group = 'entry-type'


class ComplaintLabel(EntryTypeLabel):
    name = 'complaint'


class AnswerLabel(EntryTypeLabel):
    name = 'answer'


class MotionLabel(EntryTypeLabel):
    name = 'motion'
