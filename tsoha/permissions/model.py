import inspect

from sqlalchemy import select, join

from tsoha.permissions.dsl.ast import ModelExpression, into_expression_ast
from tsoha.permissions.fluent import FluentExpression, InstanceObject


class ObjectModelMeta(type):
    @staticmethod
    
    def __new__(mcls, name, bases, attrs):
        cls = super().__new__(mcls, name, bases, attrs)

        is_model_class = lambda v: isinstance(v, ObjectModelAttribute)

        for name, value in inspect.getmembers(cls, is_model_class):
            value.register(cls, name)

        return cls


class ObjectModelAttribute:
    def __init__(self, name=None, model=None):
        self.model = name
        self.name = model
    
    def register(self, model, name):
        if self.model is None:
            self.model = model
        
        if self.name is None:
            self.name = name


class ObjectModel(metaclass=ObjectModelMeta):
    objects = {}
    permissions = {}
    
    @classmethod
    def get_object(cls, name):
        return cls.objects[name]


class ObjectDefinition(ObjectModelAttribute, FluentExpression):
    def __init__(self, schema):
        ObjectModelAttribute.__init__(self)
        FluentExpression.__init__(self, self)

        self.schema = schema
        self.relations = dict()
        self.filters = dict()
    
    def register(self, model, name):
        super().register(model, name)
        model.objects[name] = self
    
    def into_ast(self):
        return ModelExpression(self.schema.__tablename__)

    def relation(self, relation, *args, **kwargs):
        self.relations[relation] = Relation(self.model, relation, *args, **kwargs)
        return self
    
    def add_filter(self, name, *args, **kwargs):
        self.filters[name] = Filter(self.model, name, *args, **kwargs)
        return self

    def get_filter(self, name):
        return self.filters[name]
    
    def get_relation(self, relation):
        return self.relations.get(relation)
    
    def get_primary_key(self):
        return next(filter(lambda f: f.is_primary_key, self.filters.values()))


class Relation:
    def __init__(self, model, name, obj, is_singular=False, joiner=None):
        self.model = model
        self.name = name
        self._object_def = obj
        self.is_singular = is_singular
        self.joiner = joiner
    
    @property
    def object_def(self):
        if isinstance(self._object_def, str):
            self._object_def = self.model.get_object(self._object_def)
        
        return self._object_def
    
    def join(self, a, b):
        if self.joiner:
            return self.joiner(a, b)
        else:
            return select(a).select_from(join(a, b))


class Filter:
    def __init__(self, model, name, unique=None, primary_key=None):
        self.model = model
        self.name = name
        self.is_primary_key = False
        self.is_unique = False

        if primary_key:
            self.is_primary_key = True
            self.is_unique = True

            if unique is not None and unique is not True:
                raise Exception("primary keys are always unique by definition")
        
        if unique:
            self.is_unique = True


class Permission(ObjectModelAttribute):
    def __init__(self, arguments=None):
        super().__init__()
        self.arguments = arguments or []

    def register(self, model, name):
        super().register(model, name)
        model.permissions[name] = self

    def __call__(self, *values):
        if len(self.arguments) != len(values):
            raise Exception(f"permission '{self.name}' expects {len(self.arguments)} parameters, but {len(values)} given")

        return InstanceObject(
            self.name,
            map(lambda value: into_expression_ast(value, self.model), values),
        )