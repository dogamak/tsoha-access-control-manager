from tsoha import db
from tsoha.permissions.evaluate import ExpressionInterpreter, EvaluatedExpression
from tsoha.permissions.dsl.ast import InstanceExpression, into_expression_ast
from tsoha.models.permission import Permission, PermissionInstance, PermissionArgument, PermissionObjectModel


class PermissionAdder(ExpressionInterpreter):
    def __init__(self, model):
        super().__init__(model)

    def visit_instance_expression(self, expr):
        perm = Permission.query.filter(Permission.name == expr.name).first()

        if perm is None:
            perm = Permission(name=expr.name)
            db.session.add(perm)

        instance = PermissionInstance(
            permission=perm,
            expr=str(expr),
        )
        
        for arg_i, arg in enumerate(expr.arguments):
            arg = self.visit(arg)

            if isinstance(arg, EvaluatedExpression):
                objects = db.session.execute(arg.query)

                for row in objects:
                    obj = row[0]

                    argument = PermissionArgument(
                        permission_instance=instance,
                        argument_number=arg_i,
                        object_type=arg.schema.__tablename__,
                        object_id=obj.id,
                    )
                    
                    db.session.add(argument)
            elif isinstance(arg, PermissionInstance):
                arg.super_permission_id = instance.id
                arg.super_permission_parameter_number = arg_i
                db.session.add(arg)
            else:
                raise Exception()
        
        return instance
    

def add_permission(expr):
    expr = into_expression_ast(expr)

    if not isinstance(expr, InstanceExpression):
        raise Exception('expression needs to be an permission instance')

    instance = PermissionAdder(PermissionObjectModel).visit(expr)

    db.session.commit()

    return instance