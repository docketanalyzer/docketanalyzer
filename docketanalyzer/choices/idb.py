from docketanalyzer.choices.choice import Choice


class IDBArbitrationAtFiling(Choice):
    _0 = "Exempt"
    _1 = "Mandatory"
    _2 = "Missing"
    _3 = "No"
    _4 = "Voluntary"
    _5 = "Yes, Type Unknown"


class IDBArbitrationAtTermination(Choice):
    _0 = "Exempt"
    _1 = "Mandatory"
    _2 = "Missing"
    _3 = "Voluntary"


class IDBClassAction(Choice):
    _0 = "Yes"
    _1 = "No"
    _2 = "Missing"


class IDBDisposition(Choice):
    _0 = "Appeal Affirmed (Magistrate Judge)"
    _1 = "Appeal Denied (Magistrate Judge)"
    _2 = "Dismissal - Lack of Jurisdiction"
    _3 = "Dismissal - Other"
    _4 = "Dismissal - Settled"
    _5 = "Dismissal - Voluntarily"
    _6 = "Dismissal - Want of Prosecution"
    _7 = "Judgment on Award of Arbitrator"
    _8 = "Judgment on Consent"
    _9 = "Judgment on Court Trial"
    _10 = "Judgment on Default"
    _11 = "Judgment on Directed Verdict"
    _12 = "Judgment on Jury Verdict"
    _13 = "Judgment on Motion Before Trial"
    _14 = "Missing"
    _15 = "Multi District Litigation Transfer"
    _16 = "Other"
    _17 = "Remanded to State Court"
    _18 = "Remanded to U.S. Agency"
    _19 = "Statistical Closing"
    _20 = "Stayed Pending Bankruptcy"
    _21 = "Transfer to Another District"


class IDBIFP(Choice):
    _0 = "Yes"
    _1 = "No"
    _2 = "Missing"


class IDBJudgment(Choice):
    _0 = "Both"
    _1 = "Defendant"
    _2 = "Missing"
    _3 = "Plaintiff"
    _4 = "Unknown"


class IDBMDL(Choice):
    _0 = "Yes"
    _1 = "No"
    _2 = "Missing"


class IDBNatureOfJudgment(Choice):
    _0 = "Costs Only"
    _1 = "Costs and Attorney Fees"
    _2 = "Forfeiture/Foreclosure/Condemnation, etc."
    _3 = "Injunction"
    _4 = "Missing"
    _5 = "Monetary Award Only"
    _6 = "Monetary Award and Other"
    _7 = "No Monetary Award"


class IDBOrigin(Choice):
    _0 = "Appeal to District Judge of Magistrate Judge Decision"
    _1 = "Fifth Reopen"
    _2 = "Fourth Reopen"
    _3 = "Multi District Litigation"
    _4 = "Multi District Litigation Originating in the District"
    _5 = "Original Proceeding"
    _6 = "Reinstated/Reopened"
    _7 = "Remanded for Further Action"
    _8 = "Removed"
    _9 = "Second Reopen"
    _10 = "Sixth Reopen"
    _11 = "Third Reopen"
    _12 = "Transferred from Another District"


class IDBProceduralProgress(Choice):
    _0 = "After Issue Joined - After Court Trial"
    _1 = "After Issue Joined - After Jury Trial"
    _2 = "After Issue Joined - During Court Trial"
    _3 = "After Issue Joined - During Jury Trial"
    _4 = "After Issue Joined - Judgment on Motion"
    _5 = "After Issue Joined - No Court Action"
    _6 = "After Issue Joined - Other"
    _7 = "After Issue Joined - Pretrial Conference Held"
    _8 = "After Issue Joined - Request for Trial De Novo After Arbitration"
    _9 = "Before Issue Joined - Hearing Held"
    _10 = "Before Issue Joined - No Court Action"
    _11 = "Before Issue Joined - Order Decided"
    _12 = "Before Issue Joined - Order Entered"
    _13 = "Missing"


class IDBProSe(Choice):
    _0 = "Both Plaintiff & Defendant"
    _1 = "Defendant"
    _2 = "Missing"
    _3 = "None"
    _4 = "Plaintiff"


class IDBStatusCode(Choice):
    _0 = "Missing"
    _1 = "Pending Record"
    _2 = "Terminated Record"
