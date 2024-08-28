import regex as re


def notabs(text):
    return '\n'.join([x.strip() for x in text.split('\n')]).strip()


def extract_from_pattern(text, pattern, label, ignore_case=False, extract_groups={}):
    spans = []
    for match in re.finditer(pattern, text, re.IGNORECASE if ignore_case else 0):
        spans.append({
            'start': match.start(),
            'end': match.end(),
            'label': label,
        })
        for k, v in extract_groups.items():
            spans[-1][k] = {
                'start': match.start(v),
                'end': match.end(v),
            }
    return spans


def extract_attachments(text):
    pattern = r'((\(|\( )?(EXAMPLE: )?(additional )?Attachment\(?s?\)?([^:]+)?: )((([^()]+)?(\(([^()]+|(?7))*+\))?([^()]+)?)*+)\)*+'
    spans = extract_from_pattern(
        text, pattern,
        'attachment_section',
        ignore_case=True,
        extract_groups={'attachments': 6}
    )
    for span in spans:
        attachments = []
        attachments_start = span['attachments']['start']
        attachments_end = span['attachments']['end']
        attachments_str = text[attachments_start:attachments_end]
        for attachment in re.finditer(r'# (\d+) ([^#]+?)(?=, #|#|$)', attachments_str):
            attachments.append({
                'attachment_number': attachment.group(1),
                'attachment_description': attachment.group(2),
                'start': attachments_start + attachment.start(),
                'end': attachments_start + attachment.end(),
                'label': 'attachment',
            })
        span['attachments'] = attachments
    return spans


def extract_entered_date(text):
    pattern = r'\(Entered: ([\d]+/[\d]+/[\d]+)\)'
    return extract_from_pattern(text, pattern, 'entered_date')


def get_clean_name(name):
    return re.sub(r"[,.;@#?!&$]+\ *", " ", name.lower()).strip().replace('/', '_')


def mask_text_with_spans(text, spans, mapper=None):
    if mapper is None:
        mapper = lambda text, span: f"<{span['label']}>"
    spans = sorted(spans, key=lambda x: -x['start'])
    for span in spans:
        span_replace = mapper(text, span)
        text = text[:span['start']] + span_replace + text[span['end']:]
    return text


def check_span_overlap(span1, span2):
    if span1['start'] < span2['start']:
        if span1['end'] > span2['start']:
            return True
    elif span1['start'] < span2['end']:
        return True
    return False


def merge_spans(spans):
    spans = spans.copy()
    spans = sorted(spans, key=lambda x: -(x['end'] - x['start']))
    merged_spans = []
    for span in spans:
        if not any(check_span_overlap(span, s) for s in merged_spans):
            merged_spans.append(span)
    return merged_spans
