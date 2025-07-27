from .choice import Choice


class JudgeRole(Choice):
    """Judge Role choices."""

    assigned = "Assigned"
    referred = "Referred"


class JudgeType(Choice):
    """Judge Type choices."""

    district = "District Judge"
    magistrate = "Magistrate Judge"
