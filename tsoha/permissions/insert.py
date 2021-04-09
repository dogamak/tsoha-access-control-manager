from tsoha import db
from tsoha.permissions.evaluate import ExpressionInterpreter, EvaluatedExpression
from tsoha.permissions.dsl.ast import InstanceExpression, into_expression_ast, format_ast
from tsoha.models.permission import PermissionExpression, ExpressionMatch, PermissionObjectModel
from tsoha.permissions.visitor import Visitor


class PermissionAdder(ExpressionInterpreter):
    def __init__(self, model):
        super().__init__(model)

    @Visitor.visits(InstanceExpression)
    def visit_instance_expression(self, expr):
        instance = PermissionExpression(
            permission_name=expr.name,
            expression=str(expr),
        )

        for arg_i, arg_expr in enumerate(expr.arguments):
            arg_res = self.visit(arg_expr, as_dict=True)

            arg_instance = arg_res.get(PermissionAdder)

            if not arg_instance:
                arg_instance = PermissionExpression(
                    parent_expression=instance,
                    parent_expression_argument_index=arg_i,
                    expression=format_ast(arg_expr),
                )

                db.session.add(arg_instance)

            objects = db.session.execute(arg_expr.query)

            for row in objects:
                obj = row[0]

                match = ExpressionMatch(
                    expression=instance,
                    object_type=arg_expr.schema.__tablename__,
                    object_id=obj.id,
                )
                
                db.session.add(match)

        db.session.add(instance)
        
        return instance
    

def add_permission(expr):
    expr = into_expression_ast(expr)

    if not isinstance(expr, InstanceExpression):
        raise Exception('expression needs to be an permission instance')

    instance = PermissionAdder(PermissionObjectModel) \
        .visit(expr)

    db.session.commit()

    return instance