from sqlalchemy import select, join

from tsoha.permissions.dsl.ast import ModelExpression
from tsoha.permissions.fluent import FluentExpression

class ObjectModel:
    def __init__(self):
        self.objects = {}
    
    def register_object(self, name, obj):
        d = ObjectDef(self, obj)
        self.objects[name] = d
        return d
    
    def get_object(self, name):
        return self.objects[name]


class ObjectDef(FluentExpression):
    def __init__(self, model, schema):
        print(self)
        super().__init__(self)
        self.schema = schema
        self.relations = dict()
        self.filters = dict()
        self.model = model
    
    def into_ast(self):
        return ModelExpression(self.schema.__tablename__)

    def relation(self, relation, *args, **kwargs):
        self.relations[relation] = RelationDef(self.model, relation, *args, **kwargs)
        return self
    
    def add_filter(self, name, *args, **kwargs):
        self.filters[name] = FilterDef(self.model, name, *args, **kwargs)
        return self

    def get_filter(self, name):
        return self.filters[name]
    
    def get_relation(self, relation):
        return self.relations.get(relation)
    
    def get_primary_key(self):
        return next(filter(lambda f: f.is_primary_key, self.filters.values()))


class RelationDef:
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


class FilterDef:
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
