from . import extension_required

with extension_required("pacer"):
    from docketanalyzer_pacer import Pacer


__all__ = [
    "Pacer",
]
