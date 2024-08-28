class ImportExtrasError(Exception):
    pass


def lazy_load(import_path, object_name, extras=None):
    class LazyObject():
        cache = {}
        import_path = None
        object_name = None
        extras = None

        def __new__(cls, *args, **kwargs):
            if len(args) == 3 and isinstance(args[1], tuple):
                child_name, (_,), child_attrs = args
                parent_cls = cls.cls_object()
                #new_cls = type(child_name, (parent_cls,), child_attrs)
                parent_metaclass = type(parent_cls)
                new_cls = parent_metaclass(child_name, (parent_cls,), child_attrs)
                return new_cls
            return super().__new__(cls)
        
        @classmethod
        def cls_object(cls):
            if 'object' not in cls.cache:
                try:
                    module = __import__(cls.import_path, fromlist=[cls.object_name])
                    cls.cache['object'] = getattr(module, cls.object_name)
                except ModuleNotFoundError as e:
                    if cls.extras:
                        print(e)
                        message = (
                            f"\n\nThis feature requires the '{cls.extras}' extras. "
                            f"\nInstall it with: pip install 'docketanalyzer[{cls.extras}]'"
                        )
                        raise ImportExtrasError(message)
                    raise e
            return cls.cache['object']

        @property
        def object(self):
            return type(self).cls_object()
            
        def __call__(self, *args, **kwargs):
            return self.object(*args, **kwargs)

        def __getattr__(self, name):
            return getattr(self.object, name)
        
        @classmethod
        def __instancecheck__(cls, instance):
            return isinstance(instance, cls.cls_object())

        @classmethod
        def __subclasscheck__(cls, subclass):
            return issubclass(subclass, cls.cls_object())
    
    LazyObject.import_path = import_path
    LazyObject.object_name = object_name
    LazyObject.extras = extras
    return LazyObject()


def lazy_load_modules(modules, namespace):
    for module, imports in modules.items():
        for name in imports['names']:
            namespace[name] = lazy_load(module, name, extras=imports.get('extras'))