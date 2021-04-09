from sqlalchemy import event, inspect
from sqlalchemy.orm import class_mapper

from tsoha import db
from tsoha.models.permission import PermissionInstance, PermissionArgument, PermissionObjectModel
from tsoha.permissions.evaluate import ExpressionInterpreter
from tsoha.permissions.dsl.ast import InstanceExpression, JoinExpression, FilterExpression, into_expression_ast
from tsoha.permissions.visitor import Visitor

def is_permission_mapped_object(value):
    return hasattr(value, '__permission_mapping__') and getattr(value, '__permission_mapping__') is not None


def parallel_with(visitor_attr):
    def decorator(fn):
        def wrapper(self, *args, **kwargs):
            visitor = getattr(self, visitor_attr)
            other_result = getattr(visitor, fn.__name__)(*args, **kwargs)
            self_result = fn(*args, **kwargs)

            return self_result, other_result
        return wrapper
    return decorator
    


class DependencyGraphBuilder(ExpressionInterpreter):
    def __init__(self, model):
        super().__init__(model)
        self.instance = None
        self.field_dependencies = dict()
        self.argument_type_index = dict()
    
    def _add_field_dependency(self, table, field, argument):
        key = (table, field)

        if key not in self.field_dependencies:
            self.field_dependencies[key] = set([argument])
        else:
            self.field_dependencies[key].add(argument)
    
    def _add_argument_type_entry(self, table, argument):
        if table not in self.argument_type_index:
            self.argument_type_index[table] = set([ argument ])
        else:
            self.argument_type_index[table].add(argument)
    
    @Visitor.visits(InstanceExpression)
    def visit_instance_expression(self, expr):
        for arg_i, arg in enumerate(expr.arguments):
            arg_result = self.visit(arg, as_dict=True)

            evaluated = arg_result.get(ExpressionInterpreter)
            deps = arg_result.get(DependencyGraphBuilder, [])

            argument_instance = PermissionArgument.query \
                .filter(
                    PermissionArgument.permission_instance == self.instance and
                    PermissionArgument.argument_number == arg_i
                ) \
                .first()

            for table, field in deps:
                self._add_field_dependency(table, field, argument_instance)

            if not evaluated.is_singular and evaluated.object_def:
                table = evaluated.object_def.schema.__tablename__
                self._add_argument_type_entry(table, argument_instance)
        
        return None, []
    
    @Visitor.visits(JoinExpression)
    @Visitor.consumes(Visitor.original, ExpressionInterpreter)
    def visit_join_expression(self, expr, evaluated):
        return evaluated.lhs.object_def \
            .get_relation(expr.relationship) \
            .fields()

    @Visitor.visits(FilterExpression)
    @Visitor.consumes(Visitor.original, ExpressionInterpreter)
    def visit_filter_expression(self, expr, evaluated):
        table = evaluated.object_def.schema.__tablename__
        return [(table, expr.name)]
    
    def build(self, instance):
        self.instance = instance
        expr = into_expression_ast(instance.expr)
        self.visit(expr)


field_dependencies = dict()
argument_type_index = dict()


builder = DependencyGraphBuilder(PermissionObjectModel)


for instance in PermissionInstance.query.all():
    builder.build(instance)


field_dependencies = builder.field_dependencies
argument_type_index = builder.argument_type_index


# @event.listens_for(db.session, 'before_flush')
def update_permissions(session, context, instances):
    for obj in db.session.dirty:
        if not is_permission_mapped_object(obj):
            continue

        insp = inspect(obj)
        column_attrs = class_mapper(obj.__class__).column_attrs

        for attr in column_attrs:
            key = (insp.class_.__tablename__, attr.key)

            if key not in field_dependencies:
                continue

            state = insp.attrs[attr.key]

            if not (state.history.added or state.history.deleted):
                continue

            for argument in field_dependencies[key]:
                print(key, argument)