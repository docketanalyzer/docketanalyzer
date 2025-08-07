import regex as re


def extract_from_pattern(text, pattern, label, ignore_case=False, extract_groups=None):
    """Extract spans from text using a regex pattern."""
    spans = []
    for match in re.finditer(pattern, text, re.IGNORECASE if ignore_case else 0):
        spans.append(
            {
                "start": match.start(),
                "end": match.end(),
                "label": label,
            }
        )
        if extract_groups:
            for k, v in extract_groups.items():
                spans[-1][k] = {
                    "start": match.start(v),
                    "end": match.end(v),
                }
    return spans


def extract_attachments(text):
    """Parse the attachment sections from docket entries."""
    pattern = (
        r"((\(|\( )?(EXAMPLE: )?(additional )?Attachment\(?s?\)?"
        r"([^:]+)?: )((([^()]+)?(\(([^()]+|(?7))*+\))?([^()]+)?)*+)\)*+"
    )
    spans = extract_from_pattern(
        text,
        pattern,
        "attachment_section",
        ignore_case=True,
        extract_groups={"attachments": 6},
    )
    for span in spans:
        attachments = []
        attachments_start = span["attachments"]["start"]
        attachments_end = span["attachments"]["end"]
        attachments_str = text[attachments_start:attachments_end]
        for attachment in re.finditer(r"# (\d+) ([^#]+?)(?=, #|#|$)", attachments_str):
            attachments.append(
                {
                    "attachment_number": attachment.group(1),
                    "attachment_description": attachment.group(2),
                    "start": attachments_start + attachment.start(),
                    "end": attachments_start + attachment.end(),
                    "label": "attachment",
                }
            )
        span["attachments"] = attachments
    return spans
