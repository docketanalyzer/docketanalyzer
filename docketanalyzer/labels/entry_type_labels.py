from .label import Label


class EntryTypeLabel(Label):
    label_group = 'entry-type'


class AnswerLabel(EntryTypeLabel):
    name = 'answer'
    minimal_condition = lambda *xs: 'answer' in xs[-1].lower()


class ComplaintLabel(EntryTypeLabel):
    name = 'complaint'
    minimal_condition = lambda *xs: 'complaint' in xs[-1].lower()


class MotionLabel(EntryTypeLabel):
    name = 'motion'
    minimal_condition = lambda *xs: any(y in xs[-1].lower() for y in ['motion', 'petition'])


class NoticeLabel(EntryTypeLabel):
    name = 'notice'
    minimal_condition = lambda *xs: 'notice' in xs[-1].lower()


class OrderLabel(EntryTypeLabel):
    name = 'order'
    minimal_condition = lambda *xs: 'order' in xs[-1].lower()


class MinuteEntryLabel(EntryTypeLabel):
    name = 'minute entry'
    minimal_condition = lambda *xs: 'minute' in xs[-1].lower()


# move to different file
class MotionTypeLabel(EntryTypeLabel):
    parent_labels = [MotionLabel]
    minimal_condition = lambda *xs: any(y in xs[-1].lower() for y in ['motion', 'petition'])


class MotionDismissLabel(MotionTypeLabel):
    name = 'motion to dismiss'


class MotioSummaryJudgmentLabel(MotionTypeLabel):
    name = 'motion for summary judgment'
