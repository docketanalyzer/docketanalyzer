from .label import Label
from .entry_type_labels import MotionLabel


class MotionTypeLabel(Label):
    label_group = 'motion-type'
    parent_labels = [MotionLabel]
    minimal_condition = lambda *xs: any(y in xs[-1].lower() for y in ['motion', 'petition'])


class MotionDismissLabel(MotionTypeLabel):
    name = 'motion to dismiss'


class MotioSummaryJudgmentLabel(MotionTypeLabel):
    name = 'motion for summary judgment'
