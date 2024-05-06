from docketanalyzer.choices.choice import Choice


class PartyType(Choice):
    plaintiff = "Plaintiff"
    defendant = "Defendant"
    other = "Other"


class PartyEntityType(Choice):
    individual = "Individual"
    company = "Company"
    government = "Government"
    url = "URL"
    property = "Property"
    other = "Other"
