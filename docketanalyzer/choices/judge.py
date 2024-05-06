from docketanalyzer.choices.choice import Choice


class JudgeRole(Choice):
    assigned = "Assigned"
    referred = "Referred"


class JudgeType(Choice):
    district = "District Judge"
    magistrate = "Magistrate Judge"
