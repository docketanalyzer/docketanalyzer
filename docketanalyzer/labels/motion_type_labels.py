from .label import Label
from .entry_type_labels import MotionLabel


class MotionTypeLabel(Label):
    label_group = 'motion-type'
    parent_labels = [MotionLabel]
    minimal_keywords_any = ['motion', 'petition']


class MotionDismissLabel(MotionTypeLabel):
    name = 'motion to dismiss'


class MotioSummaryJudgmentLabel(MotionTypeLabel):
    name = 'motion for summary judgment'
