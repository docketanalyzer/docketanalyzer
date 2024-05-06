from docketanalyzer.choices.choice import Choice


class Disposition(Choice):
    consent_decree = "Consent Decree"
    default_judgment = "Default Judgment"
    rule_12b = "Rule 12(b) Dismissal"
    summary_judgment = "Summary Judgment"
    rule_68 = "Offer of Judgment"
    case_dismissed = "Dismissal (Other)"
    settlement = "Settlement"
    voluntary_dismissal = "Voluntary Dismissal"
    remand = "Remand"
    outbound_transfer = "Transfer"
    trial = "Trial"
    sentence = "Sentence"


class EntryType(Choice):
    complaint = "Complaint"
    information = "Information"
    indictment = "Indictment"
    answer = "Answer"
    motion = "Motion"
    notice = "Notice"
    petition = "Petition"
    stipulation = "Stipulation"
    order = "Order"
    minute_entry = "Minute Entry"
    judgment = "Judgment"
    arrest = "Arrest"
    summons = "Summons"
    warrant = "Warrant"
