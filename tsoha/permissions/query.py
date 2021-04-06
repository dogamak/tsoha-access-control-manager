from sqlalchemy import select, join, and_
from sqlalchemy.orm import aliased

from tsoha import db
from tsoha.models.permission import Permission, PermissionInstance, PermissionArgument, model
from tsoha.permissions.dsl.ast import into_expression_ast
from tsoha.permissions.evaluate import ExpressionInterpreter, EvaluatedExpression


class PermissionQueryer(ExpressionInterpreter):
    def __init__(self, model):
        super().__init__(model)
    
    def visit_instance_expression(self, expr):
        def query_builder(query, instance):
            selected = []

            for arg_i, arg in enumerate(expr.arguments):
                arg = self.visit(arg)

                if isinstance(arg, EvaluatedExpression):
                    if arg.is_wildcard:
                        continue

                    alias = aliased(PermissionArgument)
                    obj_alias = aliased(arg.schema)
                    selected.append((arg.object_def, obj_alias))

                    if arg.is_singular and arg.primary_key is not None:
                        query = join(query, alias, and_(
                            alias.permission_instance_id == instance.id,
                            alias.argument_number == arg_i,
                            alias.object_type == arg.schema.__tablename__,
                            alias.object_id == arg.primary_key,
                        ))

                        query = join(query, obj_alias, alias.object_id == obj_alias.id)
                    else:
                        a = aliased(arg.schema, alias=arg.query.subquery())

                        query = join(query, alias, and_(
                            alias.permission_instance_id == instance.id,
                            alias.argument_number == arg_i,
                            alias.object_type == arg.schema.__tablename__,
                            alias.object_id.in_(select(a.id).select_from(a)),
                        ))

                        query = join(query, obj_alias, alias.object_id == obj_alias.id)
                else:
                    sub_instance = aliased(PermissionInstance)

                    name, builder = arg

                    query = join(query, sub_instance, and_(
                        sub_instance.super_permission_id == instance.id,
                        sub_instance.super_permission_parameter_number == arg_i,
                        sub_instance.permission_id == name,
                    ))

                    query, s = builder(query, sub_instance)
                    selected += s
            
            return query, selected
        
        return expr.name, query_builder
    
    def build_query(self, expr):
        name, builder = self.visit(expr)

        instance = aliased(PermissionInstance)
        perm = aliased(Permission)

        query = join(perm, instance)

        query, selected = builder(query, instance)

        return select([ s[1] for s in selected ]).select_from(query).where(perm.name == name)


def query_permission(expr):
    expr = into_expression_ast(expr)
    query = PermissionQueryer(model).build_query(expr)
    return db.session.execute(query).all()