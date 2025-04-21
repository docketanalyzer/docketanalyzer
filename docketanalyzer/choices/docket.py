from .choice import Choice


class CaseType(Choice):
    """Case Type choices."""

    cv = "Civil"
    cr = "Criminal"


class Jurisdiction(Choice):
    """Jurisdiction choices."""

    defendant = "U.S. Government Defendant"
    diversity = "Diversity"
    federal = "Federal Question"
    local = "Local Question"
    plaintiff = "U.S. Government Plaintiff"


class JuryDemand(Choice):
    """Jury Demand choices."""

    plaintiff = "Plaintiff"
    defendant = "Defendant"
    both = "Both"
    none = "None"
