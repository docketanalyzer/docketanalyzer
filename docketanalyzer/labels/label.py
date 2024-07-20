from docketanalyzer import load_docket_index


class Label:
    name = None
    label_group = None
    inactive = False

    def __init__(self, index=None):
        if index is None:
            index = load_docket_index()
        self.index = index
    
    @property
    def slug(self):
        return self.name.lower().replace(' ', '-')
    
    @property
    def model_name(self):
        return f"docketanalyzer/label-{self.slug}"
