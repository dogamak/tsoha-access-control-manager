from sqlalchemy import select, join, and_
from sqlalchemy.orm import aliased

from tsoha import db
from tsoha.models.permission import Permission, PermissionExpression, ExpressionMatch, PermissionObjectModel
from tsoha.permissions.dsl.ast import InstanceExpression, into_expression_ast
from tsoha.permissions.evaluate import ExpressionInterpreter, EvaluatedExpression
from tsoha.permissions.visitor import Visitor


query_attr = VisitorAttribute('query')
instance_attr = VisitorAttribute('instance')


class PermissionQueryer(ExpressionInterpreter):
    def __init__(self, model):
        super().__init__(model)
    
    @Visitor.visits(InstanceExpression)
    @Visitor.consumes(Visitor.original, query_attr, instance_attr)
    def visit_instance_expression(self, expr, query, instance):
        selected = []

        for arg_i, arg in enumerate(expr.arguments):
            sub_expr = aliased(PermissionExpression)

            query = join(query, sub_expr, and_(
                sub_expr.parent_permission_id == instance.id,
                sub_expr.parent_permission_argument_index == arg_i,
            ))

            arg_dict = self.visit(
                arg,
                as_dict=True,
                provide={
                    query_attr: query,
                    instance_attr: sub_expr,
                },
            )

            if not arg_dict.get(PermissionQueryer):
                evaluated = arg_dict.get(ExpressionInterpreter)

                match = aliased(ExpressionMatch)
                object_alias = aliased(evaluated.schema)

                query = join(query, match, match.expression_id == sub_expr.id)
                query = join(query, object_alias, match.object_id == object_alias.id)

                selected.append(object_alias)
            
        return query, selected
    
    def build_query(self, expr):
        instance = aliased(PermissionExpression)

        query, selected = self.visit(
            expr,
            attr=PermissionQueryer,
            provide={
                query_attr: instance,
                instance_attr: instance,
            },
        )

        return select([ s[1] for s in selected ]) \
            .select_from(query) \
            .where(and_(
                instance.permission_name == expr.name,
                instance.parent_permission_id == None,
            ))


def query_permission(expr):
    expr = into_expression_ast(expr)
    query = PermissionQueryer(PermissionObjectModel).build_query(expr)
    return db.session.execute(query).all()

def query_expression(expr):
    expr = into_expression_ast(expr)
    evaluated = ExpressionInterpreter(PermissionObjectModel).visit(expr)
    return db.session.execute(evaluated.query).all()

def match_expression(expr, instance):
    expr = into_expression_ast(expr)
    evaluated = ExpressionInterpreter(PermissionObjectModel).visit(expr)

    if instance.__tablename__ != evaluated.schema.__tablename__:
        return False
    
    a = aliased(evaluated.schema, alias=evaluated.query.subquery())
    
    query = select(a).select_from(a).where(a.id == instance.id).exists().select()

    row = db.session.execute(query).first()[0]

    if not row:
        return False
    
    return row[0]