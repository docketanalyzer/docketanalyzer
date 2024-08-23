modules = {
    'docketanalyzer_chat.chat': ['Chat', 'ChatThread'],
}


from docketanalyzer import lazy_load_modules
lazy_load_modules(modules, globals())
