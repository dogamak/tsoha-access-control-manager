import inspect
import enum

from sqlalchemy import select, join
from sqlalchemy.orm import aliased

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
    def __init__(self, schema, **kwargs):
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
        self.relations[relation] = Relation(self, relation, *args, **kwargs)
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


class RelationKind(enum.Enum):
    ManyToOne  = 'many-to-one'
    OneToMany  = 'one-to-many'
    ManyToMany = 'many-to-many'


class Relation:
    def __init__(self, parent_obj, name, obj, many_to_one=None, one_to_many=None, secondary=None, remote_field=None, local_field=None):
        self.parent_obj = parent_obj
        self.name = name
        self._object_def = obj

        self.kind = None
        self.secondary = secondary
        self._local_field = local_field
        self._remote_field = remote_field

        if many_to_one:
            self.kind = RelationKind.ManyToOne
        
        if one_to_many:
            if self.kind is not None:
                raise Exception("only one of arguments 'many_to_one', 'one_to_many' and 'seconadry' may be present at once")
            
            self.kind = RelationKind.OneToMany
        
        if secondary is not None:
            if self.kind is not None:
                raise Exception("only one of arguments 'many_to_one', 'one_to_many' and 'seconadry' may be present at once")

            self.kind = RelationKind.ManyToMany
    
    @property
    def model(self):
        return self.parent_obj.model
    
    @property
    def object_def(self):
        if isinstance(self._object_def, str):
            self._object_def = self.model.get_object(self._object_def)
        
        for object_def in self.model.objects.values():
            if object_def.schema == self._object_def:
                return object_def
        
        return self._object_def
    
    @property
    def local_field(self):
        if self.kind not in (RelationKind.ManyToOne, RelationKind.ManyToMany):
            return None

        if self._local_field is not None:
            return self._local_field
        
        if self.kind == RelationKind.ManyToOne:
            self._local_field = self.object_def.schema.__tablename__ + '_id'

        elif self.kind == RelationKind.ManyToMany:
            self._local_field = self.parent_obj.schema.__tablename__ + '_id'
        
        return self._local_field
    
    @property
    def remote_field(self):
        if self.kind not in (RelationKind.OneToMany, RelationKind.ManyToMany):
            return None

        if self._remote_field is not None:
            return self._remote_field
        
        if self.kind == RelationKind.OneToMany:
            self._remote_field = self.parent_obj.schema.__tablename__ + '_id'
        
        elif self.kind == RelationKind.ManyToMany:
            self._remote_field = self.object_def.schema.__tablename__ + '_id'
        
        return self._remote_field
    
    def join(self, a, b):
        if self.kind == RelationKind.ManyToOne:
            from_stmt = join(a, b, getattr(a, 'id') == getattr(b, self.local_field))

        elif self.kind == RelationKind.OneToMany:
            from_stmt = join(a, b, getattr(a, self.remote_field) == getattr(b, 'id'))

        elif self.kind == RelationKind.ManyToMany:
            s = aliased(self.secondary)
            from_stmt = join(a, s, getattr(s, self.local_field) == getattr(a, 'id')) \
                .join(b, getattr(b, 'id') == getattr(s, self.remote_field))

        else:
            raise Exception()

        return select(a).select_from(from_stmt)
    
    def fields(self):
        if self.kind == RelationKind.ManyToOne:
            return [( self.parent_obj.schema.__tablename__, self.local_field )]
        elif self.kind == RelationKind.OneToMany:
            return [( self.object_def.schema.__tablename__, self.remote_field )]
        elif self.kind == RelationKind.ManyToMany:
            return [
                ( self.secondary.__tablename__, self.local_field ),
                ( self.secondary.__tablename__, self.remote_field ),
            ]
        else:
            raise Exception()


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