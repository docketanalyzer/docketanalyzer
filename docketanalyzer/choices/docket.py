from docketanalyzer.choices.choice import Choice


class CaseType(Choice):
    cv = "Civil"
    cr = "Criminal"
    md = "Other"
    mj = "Other"
    mi = "Other"
    mc = "Other"


class Jurisdiction(Choice):
    defendant = "U.S. Government Defendant"
    diversity = "Diversity"
    federal = "Federal Question"
    local = "Local Question"
    plaintiff = "U.S. Government Plaintiff"


class JuryDemand(Choice):
    plaintiff = "Plaintiff"
    defendant = "Defendant"
    both = "Both"
    none = "None"
