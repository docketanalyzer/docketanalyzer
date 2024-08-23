modules = {
    'docketanalyzer_ocr.ocr': ['extract_pages'],
}


from docketanalyzer import lazy_load_modules
lazy_load_modules(modules, globals())
