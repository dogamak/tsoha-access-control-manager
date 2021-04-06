from tsoha.permissions.dsl.ast import Visitor

from sqlalchemy import select, join
from sqlalchemy.orm import aliased


class EvaluatedExpression:
    def __init__(self, object_def=None, query=None, value=None, is_singular=None, is_literal=False, is_wildcard=False):
        self.object_def = object_def
        self.query = query
        self.is_singular = is_singular if is_singular is not None else is_literal
        self.is_literal = is_literal
        self.value = value
        self.is_wildcard = is_wildcard
        self.known_values = {}
    
    @property
    def primary_key(self):
        if not self.is_singular:
            raise Exception()
        
        filter_def = self.object_def.get_primary_key()

        if filter_def.name in self.known_values:
            return self.known_values[filter_def.name]
        
        raise Exception('primary key could not be inferred for the expression')

    @property
    def schema(self):
        return self.object_def.schema


class ExpressionInterpreter(Visitor):
    def __init__(self, model):
        self.model = model
    
    def visit_instance_expression(self, expr): 
        pass

    def visit_model_expression(self, expr):
        obj_def = self.model.get_object(expr.name)
        query = select([obj_def.schema])

        return EvaluatedExpression(object_def=obj_def, query=query)
    
    def visit_filter_expression(self, expr):
        lhs = self.visit(expr.lhs)
        value = self.visit(expr.value)

        filter_def = lhs.object_def.get_filter(expr.name)

        if filter_def is None:
            raise Exception(f"no filter '{expr.name}' defined for object '{lhs.schema.__tablename__}'")
        
        a = aliased(lhs.schema, alias=lhs.query.subquery())

        if value.is_literal:
            result = select(a).where(getattr(a, expr.name) == value.value)
        elif value.is_singular:
            result = select(a).where(getattr(a, expr.name) == value.query)
        else:
            result = select(a).where(getattr(a, expr.name).in_(value.query))

        if filter_def.is_unique:
            lhs.is_singular = True

            if value.is_literal:
                lhs.known_values[expr.name] = value.value
        
        lhs.query = result
        
        return lhs
    
    def visit_join_expression(self, expr):
        lhs = self.visit(expr.lhs)

        relation_def = lhs.object_def.get_relation(expr.name) 

        if relation_def is None:
            raise Exception(f"no relation '{expr.name}' defined for object '{lhs.schema.__tablename__}'")
        
        query = relation_def.join(relation_def.object_def.schema, aliased(lhs.schema, alias=lhs.query.subquery()))

        return EvaluatedExpression(
            object_def=relation_def.object_def,
            is_singular=relation_def.is_singular and lhs.is_singular,
            query=query,
        )
    
    def visit_wildcard_expression(self, _expr):
        return EvaluatedExpression(is_wildcard=True)
    
    def visit_integer(self, value):
        return EvaluatedExpression(is_literal=True, value=value)
    
    def visit_text(self, value):
        return EvaluatedExpression(is_literal=True, value=value)