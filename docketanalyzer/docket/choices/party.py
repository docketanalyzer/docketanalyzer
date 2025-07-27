from .choice import Choice


class PartyType(Choice):
    """Party Type choices."""

    plaintiff = "Plaintiff"
    defendant = "Defendant"
    other = "Other"


class PartyEntityType(Choice):
    """Party Entity Type choices."""

    individual = "Individual"
    company = "Company"
    government = "Government"
    other = "Unclassified (other)"
