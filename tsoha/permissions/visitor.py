import inspect


class VisitorAttributeDict(dict):
    def get(self, key, default=None):
        key = VisitorAttribute.resolve(key)
        return super().get(key, default)


class VisitorAttribute:
    def __init__(self, label, default=False):
        self.label = label
        self.default = default
    
    def __repr__(self):
        if self.default:
            return f'<VisitorAttribute {repr(self.label)} (default)>'
        else:
            return f'<VisitorAttribute {repr(self.label)}>'
    
    @staticmethod
    def resolve(attr):
        if inspect.isclass(attr) and issubclass(attr, Visitor):
            return attr.default
        elif isinstance(attr, VisitorAttribute):
            return attr
        
        raise Exception(f'expected a VisitorAttribute, got {type(attr)}')


class VisitorMeta(type):
    @staticmethod
    def __new__(mcls, name, bases, attrs):
        cls = super().__new__(mcls, name, bases, attrs)

        cls._visitors = []
        cls._superclass = []
        cls.default = VisitorAttribute(name, default=True)

        for name, value in inspect.getmembers(cls, callable):
            if not hasattr(value, '_visits'):
                continue

            if not hasattr(value, '_provides'):
                value._provides = cls.default
            
            if not hasattr(value, '_consumes') and len(inspect.signature(value).parameters) == 2:
                value._consumes = [ original ]

            cls._visitors.append(value)

        return cls
    
    def consumes(cls, *attributes):
        def decorator(fn):
            fn._consumes = list(map(VisitorAttribute.resolve, attributes))

            return fn
        
        return decorator

    def provides(cls, attribute):
        def decorator(fn):
            fn._provides = attribute
            return fn
        
        return decorator

    def visits(cls, visits):
        def decorator(fn):
            fn._visits = visits
            return fn
        
        return decorator


original = VisitorAttribute('Visitor.original')

class Visitor(metaclass=VisitorMeta):
    _visitors = []
    _superclass = []

    def visit(self, value, attr=None, as_dict=False):
        results = VisitorAttributeDict()

        results[original] = value

        for class_ in self.__class__.mro()[::-1]:
            if not issubclass(class_, Visitor):
                continue

            for visitor in class_._visitors:
                if not isinstance(value, visitor._visits):
                    continue

                args = [ results[attr] for attr in visitor._consumes ]
                self._superclass.append(class_)
                results[visitor._provides] = visitor(self, *args)
                self._superclass.pop()
        
        if attr is None:
            if self._superclass:
                attr = self._superclass[-1].default
            else:
                attr = self.default
        else:
            attr = VisitorAttribute.resolve(attr)
        
        if not as_dict:
            return results.get(attr)

        return results

Visitor.original = original