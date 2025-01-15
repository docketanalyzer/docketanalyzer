import regex as re


def notabs(text):
    """Remove leading/trailing whitespace on each line."""
    return '\n'.join([x.strip() for x in text.split('\n')]).strip()


def extract_from_pattern(text, pattern, label, ignore_case=False, extract_groups={}):
    """Extract spans from text using a regex pattern."""
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


def mask_text_with_spans(text, spans, mapper=None):
    """Provide a list of spans and mask the text with a custom function."""
    if not spans:
        return text
    if mapper is None:
        mapper = lambda text, span: f"<{span['label']}>"
    spans = sorted(spans, key=lambda x: -x['start'])
    parts, last_end = [], len(text)
    
    for span in spans:
        parts.append(text[span['end']:last_end])
        parts.append(mapper(text, span))
        last_end = span['start']
    if last_end > 0:
        parts.append(text[:last_end])
    return ''.join(reversed(parts))


def check_span_overlap(span1, span2):
    """Check if two spans overlap."""
    if span1['start'] < span2['start']:
        if span1['end'] > span2['start']:
            return True
    elif span1['start'] < span2['end']:
        return True
    return False


def merge_spans(spans):
    """Merge spans that don't overlap, prioritizing longer spans."""
    if not spans:
        return []
    sorted_spans = sorted(spans, key=lambda x: (x['start'], -(x['end'] - x['start'])))
    merged = [sorted_spans[0]]
    
    for span in sorted_spans[1:]:
        if span['start'] >= merged[-1]['end']:
            merged.append(span)
    return merged


def escape_markdown(text):
    """Escape special characters in Markdown."""
    markdown_chars = r'([\*\_\{\}\[\]\(\)\#\+\-\.\!\|])'
    return re.sub(markdown_chars, r'\\\1', text)


def extract_attachments(text):
    """Parse the attachment sections from docket entries."""
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
    """Parse the entered date from docket entries."""
    pattern = r'\(Entered: ([\d]+/[\d]+/[\d]+)\)'
    return extract_from_pattern(text, pattern, 'entered_date')


def make_simple_text(text):
    """Strip entered dates and attachments from docket entry text."""
    attachments = extract_attachments(text)
    entered_date = extract_entered_date(text)
    text = mask_text_with_spans(text, attachments + entered_date, mapper=lambda text, span: ' ')
    text = ' '.join(text.split())
    return text


def get_clean_name(name):
    """Prepro utility for simplifying and standardizing names."""
    return re.sub(r"[,.;@#?!&$]+\ *", " ", name.lower()).strip().replace('/', '_')
