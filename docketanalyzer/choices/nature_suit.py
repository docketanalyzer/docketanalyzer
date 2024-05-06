from docketanalyzer.choices.choice import Choice


class NatureSuit(Choice):
    _110 = (
            '110 Insurance',
            {'section': 'Contract', 'description': 'Action alleging breach of insurance contract, tort claim, or other cause related to an insurance contract, except for maritime insurance contracts.'},
    )
    _111 = (
            '111 Miscellaneous',
            {'section': None, 'description': 'This nature of suit has been depreciated by the courts.'},
    )
    _120 = (
            '120 Marine',
            {'section': 'Contract', 'description': 'Action (Admiralty or Maritime) based on service, employment, insurance or other contracts relating to maritime vessels and other maritime contractual matters.'},
    )
    _130 = (
            '130 Miller Act',
            {'section': 'Contract', 'description': 'Action based on performance and payment bonds agreed to by contractors on federal construction projects as required under the Miller Act, 40 USC Â§3131-3134.'},
    )
    _140 = (
            '140 Negotiable Instrument',
            {'section': 'Contract', 'description': 'Action relating to an agreement to pay a specific amount of money, including promissory notes, loan agreements and checks.'},
    )
    _150 = (
            '150 Recovery Of Overparyment & Enforcement Of Judgment',
            {'section': 'Contract', 'description': 'Action to recover debt owed to the United States, including enforcement of judgments, based on overpayments and restitution agreements involving matters other than Medicare benefits, student loans and veteransâ\x80\x99 benefits.'},
    )
    _151 = (
            '151 Medicare Act',
            {'section': 'Contract', 'description': 'Action relating to Medicare payments, including actions for payments of benefits, to recover overpayments, and for judicial review of administrative decisions.'},
    )
    _152 = (
            '152 Recovery Of Defaulted Student Loans (Excl. Veterans)',
            {'section': 'Contract', 'description': 'Action to recover debt owed to the United States from defaulted student loan.'},
    )
    _153 = (
            '153 Recovery Of Overpayment Of Veteran S Benefits',
            {'section': 'Contract', 'description': 'Action relating to payments of veteransâ\x80\x99 benefits, primarily including actions to recover overpayments.'},
    )
    _160 = (
            '160 Stockholders Suits',
            {'section': 'Contract', 'description': 'Action brought by stockholder(s) of a corporation (including both stockholder derivative suits and direct actions based on plaintiffâ\x80\x99s rights as a stockholder), usually alleging claims based on contract and/or tort law and/or fiduciary obligations.'},
    )
    _190 = (
            '190 Other Contract',
            {'section': 'Contract', 'description': 'Action primarily based on rights and obligations under a contract not classifiable elsewhere under the specific natures of suit under â\x80\x9cContract.â\x80\x9d'},
    )
    _195 = (
            '195 Contract Product Liability',
            {'section': 'Contract', 'description': 'Action concerning damages caused by a defective product, not primarily involving personal injury or property damage, and based primarily on breach of contract, breach of warranty, misrepresentation, and/or violation of consumer protection laws.'},
    )
    _196 = (
            '196 Franchise',
            {'section': 'Contract', 'description': 'Action arising from a dispute over a franchise agreement, typically alleging breach of contract, misrepresentation or unfair trade practices.'},
    )
    _210 = (
            '210 Land Condemnation',
            {'section': 'Real Property', 'description': 'Action by a governmental entity to take privately-owned real property (land or buildings) for public use for compensation.'},
    )
    _220 = (
            '220 Foreclosure',
            {'section': 'Real Property', 'description': 'Action to enjoin foreclosure on real property by mortgage lender.'},
    )
    _230 = (
            '230 Rent Lease & Ejectment',
            {'section': 'Real Property', 'description': 'Action for rental or lease payments owed on real property and/or to eject a party occupying real property illegally.'},
    )
    _240 = (
            '240 Torts To Land',
            {'section': 'Real Property', 'description': 'Action alleging trespass to land, nuisance, contamination or other unlawful entry on or interference with real property possessed by another.'},
    )
    _245 = (
            '245 Tort Product Liability',
            {'section': 'Real Property', 'description': 'Action alleging harm by an unsafe product based on negligence, breach of warranty, misrepresentation, and strict tort liability.'},
    )
    _290 = (
            '290 All Other Property',
            {'section': 'Real Property', 'description': 'Action primarily based on unlawful conduct relating to real property that cannot be classified under any other nature of suit.'},
    )
    _310 = (
            '310 Airplane',
            {'section': 'Torts/Personal Injury', 'description': 'Action alleging personal injury or wrongful death from an air crash or other occurrence involving an airplane.'},
    )
    _315 = (
            '315 Airplane Product Liability',
            {'section': 'Torts/Personal Injury', 'description': 'Action alleging personal injury or death from an air crash or other occurrence involving an airplane and caused by a defective product.'},
    )
    _320 = (
            '320 Assault, Libel, & Slander',
            {'section': 'Torts/Personal Injury', 'description': 'Action alleging intentional acts of assault, libel, trade libel or slander by a private party.'},
    )
    _330 = (
            '330 Federalemployers Liability',
            {'section': 'Torts/Personal Injury', 'description': 'Action for personal injury or wrongful death brought by a railroad employee or his survivors under the Federal Employersâ\x80\x99 Liability Act (FELA), 45 USC Â§51, et. seq.'},
    )
    _340 = (
            '340 Marine',
            {'section': 'Torts/Personal Injury', 'description': 'Action (Admiralty and Maritime) alleging personal injury or death from an accident involving a water vessel or harbor/dock facilities, including suits brought under the Jones Act and the Limitation of Liability Act.'},
    )
    _345 = (
            '345 Marine Product Liability',
            {'section': 'Torts/Personal Injury', 'description': 'Action (Admiralty and Maritime) alleging personal injury or wrongful death from an accident involving a water vessel or harbor/dock facilities and caused by a defective product.'},
    )
    _350 = (
            '350 Motor Vehicle',
            {'section': 'Torts/Personal Injury', 'description': 'Action alleging personal injury or wrongful death from negligence involving a motor vehicle but not caused by a defective product.'},
    )
    _355 = (
            '355 Motor Vehicle Product Liability',
            {'section': 'Torts/Personal Injury', 'description': 'Action alleging personal injury or wrongful death involving a motor vehicle and caused by a defective product.'},
    )
    _360 = (
            '360 Other Personal Injury',
            {'section': 'Torts/Personal Injury', 'description': 'Action primarily based on personal injury or death caused by negligence or intentional misconduct, including suits brought against the United States under the Federal Tort Claims Act, and which cannot be classified under any other nature of suit.'},
    )
    _362 = (
            '362 Personal Injury- Medical Malpractice',
            {'section': 'Torts/Personal Injury', 'description': 'Action alleging personal injury or wrongful death caused by negligence in medical care provided by a doctor or other health care professional.'},
    )
    _365 = (
            '365 Personal Injury- Product Liability',
            {'section': 'Torts/Personal Injury', 'description': 'Action alleging personal injury or death resulting from a defective product.'},
    )
    _367 = (
            '367 Personal Injury - Health Care/Pharmaceutical Personal Injury/Product Liability',
            {'section': 'Torts/Personal Injury', 'description': 'Action alleging personal injury or death caused by a defective medical or pharmaceutical product.'},
    )
    _368 = (
            '368 Asbestos Personal Injury Product Liability',
            {'section': 'Torts/Personal Injury', 'description': 'Action alleging personal injury or death caused by exposure to asbestos products.'},
    )
    _370 = (
            '370 Other Fraud',
            {'section': 'Personal Property', 'description': 'Action primarily based on fraud relating to personal property that cannot be classified under any other nature of suit.'},
    )
    _371 = (
            '371 Truth In Lending',
            {'section': 'Personal Property', 'description': 'Action alleging violation of the federal Truth in Lending Act arising from consumer loan transactions involving personal property including automobile loans and revolving credit accounts.'},
    )
    _375 = (
            '375 False Claims Act',
            {'section': 'Other Statutes', 'description': 'Action filed by private individuals alleging fraud against the U.S. Government under 31 USC Â§3729.'},
    )
    _376 = (
            '376 376 Qui Tam (31 U.S.C. 3729(A))',
            {'section': 'Other Statutes', 'description': 'Action brought under the False Claims Act by private persons (also known as "whistleblowers") on their own behalf and on behalf of the United States to recover damages against another person or entity that acted fraudulently in receiving payments or property from, or avoiding debts owed to, the United States Government, 31 USC Â§3730.'},
    )
    _380 = (
            '380 Other Personal Property Damage',
            {'section': 'Personal Property', 'description': 'Action primarily based on damage to personal property caused by harmful conduct such as negligence, misrepresentation, interference with business relationships or unfair trade practices.'},
    )
    _385 = (
            '385 Property Damage Product Liability',
            {'section': 'Personal Property', 'description': 'Action alleging damage to personal property caused by a defective product.'},
    )
    _400 = (
            '400 State Reapportionment',
            {'section': 'Other Statutes', 'description': 'Action filed under the Reapportionment Act of 1929 Ch. 28, 46 Stat. 21, 2 USC Â§2a.'},
    )
    _410 = (
            '410 Antitrust',
            {'section': 'Other Statutes', 'description': 'Action brought under the Clayton Act 15 USC Â§12 - 27 alleging undue restriction of trade and commerce by designated methods that limit free competition in the market place amongst consumers such as anti-competitive price discrimination, corporate mergers, interlocking directorates or tying and exclusive dealing contracts.'},
    )
    _422 = (
            '422 Appeal 28 Usc 158',
            {'section': 'Bankruptcy', 'description': 'All appeals of previous bankruptcy decisions filed under 28 USC Â§158.'},
    )
    _423 = (
            '423 Withdrawal 28 Usc 157',
            {'section': 'Bankruptcy', 'description': 'Action held in bankruptcy court requesting withdrawal under the provisions of 28 USC Â§157.'},
    )
    _430 = (
            '430 Banks And Banking',
            {'section': 'Other Statutes', 'description': 'Action filed under the Federal Home Loan Bank Act 12:1421-1449, Home Owners Loan Act 12:1461 or Federal Reserve Acts 12:142 et seq.'},
    )
    _440 = (
            '440 Other Civil Rights',
            {'section': 'Civil Rights', 'description': 'Action alleging a civil rights violation other than the specific civil rights categories covered by other codes or a violation related to prison.\nExample: Action alleging excessive force by police incident to an arrest.'},
    )
    _441 = (
            '441 Voting',
            {'section': 'Civil Rights', 'description': 'Action filed under Civil Rights Act, 52 USC Â§10101, and Voting Rights Act, 52 USC Â§10301.'},
    )
    _442 = (
            '442 Employment',
            {'section': 'Civil Rights', 'description': 'Action filed under Age Discrimination in Employment Act 29:621:634, Equal Employment Opportunity Act (Title VII) 42:2000E, Performance Rating Act of 1950 5:4303.'},
    )
    _443 = (
            '443 Housing/Accommodations',
            {'section': 'Civil Rights', 'description': 'Action filed under the Fair Housing Act (Title VII), 42 USC Â§3601 & 3602.'},
    )
    _444 = (
            '444 Welfare',
            {'section': None, 'description': 'This nature of suit has been depreciated by the courts.'},
    )
    _445 = (
            '445 Amer W/Disabilities-Employment',
            {'section': 'Civil Rights', 'description': 'Action of discrimination against an employee with disabilities of any type in the work place, filed under 42 USC Â§12117.'},
    )
    _446 = (
            '446 Amer W/Disabilities - Other',
            {'section': 'Civil Rights', 'description': 'Action of discrimination against an individual with disabilities in areas other than employment, filed under 42 USC Â§12133 (exclusion or discrimination in provision of services, programs or activities of a public entity) or 42 USC Â§12188 (public accommodations).'},
    )
    _448 = (
            '448 Education',
            {'section': 'Civil Rights', 'description': 'Action filed under the Individuals with Disabilities Educations Act, 20 USC Â§1401 and Title IX of the Education Amendment of 1972, 20 USC Â§1681 et seq.'},
    )
    _450 = (
            '450 Commerce',
            {'section': 'Other Statutes', 'description': 'Action filed under the Interstate Commerce Acts 49:1 et seq., 49:301.'},
    )
    _460 = (
            '460 Deportation',
            {'section': 'Other Statutes', 'description': 'Action filed under the Immigration Acts (Habeas Corpus & Review) 8:1101/18:1546'},
    )
    _462 = (
            '462 Naturalization Application',
            {'section': 'Immigration', 'description': 'Action seeking review of denial of an application for naturalization [8 USC Â§1447(b)] or alleging failure to make a determination regarding an application for naturalization [8 USC Â§1421(c)].'},
    )
    _463 = (
            '463 Habeas Corpus - Alien Detainee',
            {'section': 'Prisoner Petitions - Habeas Corpus', 'description': 'Immigration habeas petition under 28 USC Â§2241. All cases filed with this nature of suit code are restricted to case participants and public terminals. Petition is filed by an alien detainee.'},
    )
    _465 = (
            '465 Other Immigration Actions',
            {'section': 'Immigration', 'description': 'Action (Immigration-related) that do not involve Naturalization Applications or petitions for Writ of Habeas Corpus, such as complaints alleging failure to adjudicate an application to adjust immigration status to permanent resident.'},
    )
    _470 = (
            '470 Racketeer Influenced And Corrupt Organizations',
            {'section': 'Other Statutes', 'description': 'Racketeer Influenced and Corrupt Organization Act, RICO 18:1961-1968.'},
    )
    _480 = (
            '480 Consumer Credit',
            {'section': 'Other Statutes', 'description': 'Action filed under the Fair Credit Reporting Act, 15 USC 1681n or 15 USC 1681o, and the Fair Debt Collection Practices Act, 15 USC Â§1692k.'},
    )
    _485 = (
            '485 Telephone Consumer Protection Act (Tcpa)',
            {'section': 'Other Statutes', 'description': 'Action filed under the Telephone Consumer Protection Act 47 USC Â§227.'},
    )
    _490 = (
            '490 Cable/Sat Tv',
            {'section': 'Other Statutes', 'description': 'Action filed involving unauthorized reception of cable/satellite TV service under 47 USC Â§553 (unauthorized reception of cable/satellite TV), or 47 USC Â§605 (e)(3) (unauthorized use or publication of a communication).'},
    )
    _510 = (
            '510 Motions To Vacate Sentence',
            {'section': 'Prisoner Petitions - Habeas Corpus', 'description': 'Action by a prisoner to vacate or modify a sentence imposed in federal court, other than a death sentence, under 28 USC Â§2255.'},
    )
    _530 = (
            '530 General',
            {'section': 'Prisoner Petitions - Habeas Corpus', 'description': 'Action by a federal or state prisoner currently in custody challenging the legality of confinement or other punishment. This includes claims alleging illegalities that occurred in trial (for example, ineffective assistance of counsel), sentencing (including fines and restitution orders), or disciplinary proceedings in prison (for example, loss of good time credits). Habeas petition under 28 USC Â§2254 or prisoner habeas under 28 USC Â§2241.'},
    )
    _535 = (
            '535 Death Penalty',
            {'section': 'Prisoner Petitions - Habeas Corpus', 'description': 'Action by a federal or state prisoner challenging a death sentence.'},
    )
    _540 = (
            '540 Mandamus & Other',
            {'section': 'Prisoner Petitions - Other', 'description': 'Action by prisoner currently in custody for a writ of mandamus to compel action by a judge or government official relating to the prisonerâ\x80\x99s confinement, including conditions of confinement. This category also includes any actions other than mandamus brought by a prisoner currently in custody, whether or not it relates to his confinement, if it is not classifiable under any other nature of suit category under Prisoner Petitions (for example, action by prisoner to recover property taken by the government in a criminal case).'},
    )
    _550 = (
            '550 Civil Rights',
            {'section': 'Prisoner Petitions - Other', 'description': 'Action by current or former prisoner alleging a civil rights violation by corrections officials that is not related to a condition of prison life.'},
    )
    _555 = (
            '555 Prison Condition',
            {'section': 'Prisoner Petitions - Other', 'description': 'Action by current prisoner, or former prisoner or their families alleging a civil rights, Federal Tort Claims Act, or state law claim with respect to a condition of prison life, whether general circumstances or particular episodes. Examples: inadequate medical care or excessive force by prison guards. Includes non-habeas actions by alien detainees alleging unlawful prison conditions.'},
    )
    _560 = (
            '560 Conditions Of Confinement',
            {'section': 'Prisoner Petitions - Other', 'description': 'Action by former prisoner who was involuntarily committed to a non- criminal facility after expiration of his or her prison term alleging unlawful conditions of confinement while in the non-criminal facility. This category includes, for example, an action by a former prisoner classified as a Sexually Dangerous Person or Sexually Violent Predator alleging civil rights violations during his detention in a medical facility.'},
    )
    _610 = (
            '610 Agriculture',
            {'section': None, 'description': 'This nature of suit has been depreciated by the courts.'},
    )
    _620 = (
            '620 Other Food & Drug',
            {'section': None, 'description': 'This nature of suit has been depreciated by the courts.'},
    )
    _625 = (
            '625 Drug Related Seizure Of Property 21 Usc 881 630 Liquor Laws',
            {'section': 'Forfeiture/Penalty', 'description': 'Action (Forfeiture) by which property itself is accused of wrongdoing and is forfeited to the government as a result.'},
    )
    _640 = (
            '640 Rr & Truck',
            {'section': None, 'description': 'This nature of suit has been depreciated by the courts.'},
    )
    _650 = (
            '650 Airline Regulations',
            {'section': None, 'description': 'This nature of suit has been depreciated by the courts.'},
    )
    _660 = (
            '660 Occupational Safety/Health',
            {'section': None, 'description': 'This nature of suit has been depreciated by the courts.'},
    )
    _690 = (
            '690 Other',
            {'section': 'Forfeiture/Penalty', 'description': "Action primarily based on Acts or Bills that cannot be classified under any other nature of suit, such as:\n\nEndangered Species Act,\nFederal Hazardous Substance Act 15:1261,\nGame & Wildlife Act 15:256C et seq. (Penalty),\nFederal Trade Commission Act 15:41-51 (Penalty),\nFederal Coal Mine Health & Safety Act 30:801 et seq. (Penalty),\nLoad Line Act 46:85-85G,\nMcGuire Bill (Federal Fair Trade) 15:45L Penalty,\nMarihuana Tax Act 50 STAT 551,\nMotorboat Act 46:526-526T,\nNational Traffic & Motor Vehicle Safety Act penalty 49:1655,\nVeterans' Benefit Act,\nTitle 38 Penalty."},
    )
    _710 = (
            '710 Fair Labor Standards Act',
            {'section': 'Labor', 'description': 'Action relating to non-union workplace related disputes filed under the Fair Labor Standards Act, 29 USC Â§201 including but not limited to wage discrimination, paid leave, minimum wage and overtime pay.'},
    )
    _720 = (
            '720 Labor/Management Relations',
            {'section': 'Labor', 'description': 'Action relating to disputes between labor unions and employers as well as all petitions regarding actions of the Nation Labor Relations Board (NLRB).'},
    )
    _730 = (
            '730 Labor/Management Reporting & Disclosure Act',
            {'section': None, 'description': 'This nature of suit has been depreciated by the courts.'},
    )
    _740 = (
            '740 Railway Labor Act',
            {'section': 'Labor', 'description': 'Action relating to disputes filed under the Railway Labor Act, 45 USC Â§151 including labor disputes, individual claims, and response to sanctions.'},
    )
    _751 = (
            '751 Family And Medical Leave Act',
            {'section': 'Labor', 'description': 'Action filed under the Family Medical Leave Act, 29 USC Â§2601.'},
    )
    _790 = (
            '790 Other Labor Litigation',
            {'section': 'Labor', 'description': 'Action primarily based on labor disputes not addressed by other NOS codes (includes Labor/Management Reporting and Disclosure Act).'},
    )
    _791 = (
            '791 Employee Retirement Income Security Act',
            {'section': 'Labor', 'description': 'Action filed under the Employee Retirement Income Security Act, 29 USC Â§1132 by individuals and labor organizations.'},
    )
    _810 = (
            '810 Selective Service',
            {'section': None, 'description': 'This nature of suit has been depreciated by the courts.'},
    )
    _820 = (
            '820 Copyrights',
            {'section': 'Property Rights', 'description': 'Action filed in support or to dispute a copyright claim.'},
    )
    _830 = (
            '830 Patent',
            {'section': 'Property Rights', 'description': 'Action filed in support or to dispute a patent claim.'},
    )
    _835 = (
            '835 Patent Abbreviated New Drug Application (Anda)',
            {'section': 'Property Rights', 'description': 'Action filed in support or to dispute a patent claim involving an Abbreviated New Drug Application (ANDA). These cases are also known as â\x80\x9cHatch-Waxmanâ\x80\x9d cases.'},
    )
    _840 = (
            '840 Trademark',
            {'section': 'Property Rights', 'description': 'Action filed in support or to dispute a trademark claim.'},
    )
    _850 = (
            '850 Securities/Commodities/Exchange',
            {'section': 'Other Statutes', 'description': 'Action filed under Small Business Investment Act 15:681, Securities Exchange Act 15:78, Securities Act 15:77, Investment Advisers Act 15:80B(1-21).'},
    )
    _861 = (
            '861 Hia (1395Ff)',
            {'section': 'Social Security', 'description': 'Action filed with regard to social security benefits associated with Health Insurance Part A Medicare.'},
    )
    _862 = (
            '862 Black Lung (923)',
            {'section': 'Social Security', 'description': 'Action filed with regard to social security benefits provided for those who contracted Black Lung or their beneficiaries.'},
    )
    _863 = (
            '863 Diwc/Diww (405(G))',
            {'section': 'Social Security', 'description': 'Action filed with regard to social security benefits provided to disabled individuals: worker or child, or widow.'},
    )
    _864 = (
            '864 Ssid Title Xvi',
            {'section': 'Social Security', 'description': 'Action filed with regard to social security benefits provided to Supplemental Security Income Disability under Title XVI.'},
    )
    _865 = (
            '865 Rsi (405(G))',
            {'section': 'Social Security', 'description': 'Action filed with regard to social security benefits provided for Retirement, Survivor Insurance under 42 USC Â§405.'},
    )
    _870 = (
            '870 Taxes (U.S. Plaintiff Or Defendant)',
            {'section': 'Federal Tax Suits', 'description': 'Action filed under the Internal Revenue Code (General).'},
    )
    _871 = (
            '871 Irs-Third Party 26 Usc 7609',
            {'section': 'Federal Tax Suits', 'description': 'Action filed under the Internal Revenue Code - Tax Reform Act of 1976 (P.L. 94-455) Third Party.'},
    )
    _875 = (
            '875 Customer Challenge 12 Usc 3410',
            {'section': None, 'description': 'This nature of suit has been depreciated by the courts.'},
    )
    _880 = (
            '880 Defend Trade Secrets Act Of 2016 (Dtsa)',
            {'section': 'Property Rights', 'description': 'Action filed in support or to dispute a trade secret misappropriation.'},
    )
    _890 = (
            '890 Other Statutory Actions',
            {'section': 'Other Statutes', 'description': 'Action primarily based on Statutes that cannot be classified under any other nature of suit, such as:\n\nForeign Agents Registration Act 22:611- 621,\nKlamath Termination Act 25:564-564W-L,\nFederal Aid Highway Act 23:101-142,\nFederal Corrupt Practices Act 2:241-256,\nFederal Election Campaign Act,\nHighway Safety Act 23:401 Immigration & Nationality Act 8:1503,\nNatural Gas Pipeline Safety Act 49:1671-1700,\nNaturalization Acts 8:1421/18:911, 1015, 1421, et seq., 3282 or\nFederal Aviation Act 49:1301 et seq.'},
    )
    _891 = (
            '891 Agricultural Acts',
            {'section': 'Other Statutes', 'description': 'Action filed under the Federal Crop Insurance Act 7:1501-1550, Commodity Credit Corporation Act 15:713A-L & 4.'},
    )
    _892 = (
            '892 Economic Stabilization Act',
            {'section': None, 'description': 'This nature of suit has been depreciated by the courts.'},
    )
    _893 = (
            '893 Environmental Matters',
            {'section': 'Other Statutes', 'description': 'Action filed under\n\nAir Pollution Control Act 42:1857-57L,\nClean Air Act 42:1857:57L,\nFederal Environment Pesticide Control Act,\nFederal Insecticide, Fungicide & Rodenticide Act 7:135,\nFederal Water Pollution Control Act 33:1151 et seq.,\nLand & Water Conservation Fund Act 16:4602,460 1-4,\nMotor Vehicle Air Pollution Control Act 42:1857F-1-8,\nNational Environmental Policy Act 42:4321, 4331-35G, 4341-47,\nRiver & Harbor Act penalty 3:401-437, 1251.'},
    )
    _894 = (
            '894 Energy Allocation Act',
            {'section': None, 'description': 'This nature of suit has been depreciated by the courts.'},
    )
    _895 = (
            '895 Freedom Of Information Act',
            {'section': 'Other Statutes', 'description': 'Action filed under the Freedom of Information Act 5:552.'},
    )
    _896 = (
            '896 Arbitration',
            {'section': 'Other Statutes', 'description': 'Action involving actions to confirm or modify arbitration awards filed under Title 9 of the U.S. Code.'},
    )
    _899 = (
            '899 Administrative Procedure Act/Review Or Appeal Of Agency Decision',
            {'section': 'Other Statutes', 'description': 'Action filed under the Administrative Procedures Act, 5 USC Â§701, or civil actions to review or appeal a federal agency decision.'},
    )
    _900 = (
            '900 Appeal Of Fee Determination Under Equal Access To Justice Act',
            {'section': None, 'description': 'This nature of suit has been depreciated by the courts.'},
    )
    _950 = (
            '950 Constitutionality Of State Statutes',
            {'section': 'Other Statutes', 'description': 'Action drawing into question the constitutionality of a federal or state statute filed under (Rule 5.1). Rule 5.1 implements 28 USC Â§2403.'},
    )
    _990 = (
            '990 Other',
            {'section': None, 'description': 'This nature of suit has been depreciated by the courts.'},
    )
    _999 = (
            '999 Miscellaneous Cases',
            {'section': None, 'description': 'This nature of suit has been depreciated by the courts.'},
    )
