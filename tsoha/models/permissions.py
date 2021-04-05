from tsoha import db
from tsoha.models import Base, User, Group, GroupMembership
from tsoha.permissions.expression import ObjectModel, ExpressionVisitor, Parser, tokenize, InstanceExpression, ExpressionInterpreter, EvaluatedExpression, PermissionObject, into_expression_ast, WildcardExpression

from sqlalchemy import select, join, exists, not_, and_
from sqlalchemy.orm import aliased

class Permission(db.Model):
    name = db.Column(db.String, primary_key=True)

class PermissionInstance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    permission_id = db.Column(db.String, db.ForeignKey(Permission.name), nullable=False)
    expr = db.Column(db.String, nullable=False)
    super_permission_id = db.Column(db.Integer, db.ForeignKey(id))
    super_permission_parameter_number = db.Column(db.Integer)

    permission = db.relationship(Permission)
    super_permission = db.relationship('PermissionInstance', remote_side=[id])

class PermissionArgument(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    permission_instance_id = db.Column(db.Integer, db.ForeignKey(PermissionInstance.id), nullable=False)
    argument_number = db.Column(db.Integer, nullable=False)
    object_type = db.Column(db.String, nullable=False)
    object_id = db.Column(db.Integer, nullable=False)

    permission_instance = db.relationship(PermissionInstance)

model = ObjectModel()

secondary_join = lambda s:   lambda a, q: select([a]).select_from(join(q, s).join(a))
join_on_remote = lambda key: lambda a, q: select([a]).select_from(join(q, a, getattr(a, key) == q.id))
join_on_local  = lambda key: lambda a, q: select([a]).select_from(join(q, a, getattr(q, key) == a.id))

model.register_object('user', User) \
    .relation('groups', 'group', joiner=secondary_join(GroupMembership)) \
    .relation('subordinates', 'user', joiner=join_on_remote('supervisor_id')) \
    .relation('supervisor', 'user', joiner=join_on_local('supervisor_id')) \
    .add_filter('id', primary_key=True) \
    .add_filter('username', unique=True)

model.register_object('group', Group) \
    .relation('members', 'user', joiner=secondary_join(GroupMembership)) \
    .relation('subgroups', 'group', joiner=join_on_remote('parent_id')) \
    .relation('parent', 'group', joiner=join_on_local('parent_id'), is_singular=True) \
    .add_filter('id', primary_key=True)

user = model.get_object('user')
group = model.get_object('group')

create_user = PermissionObject(
    model,
    'create_user',
    ['current_user', 'target_group'],
    'user {current_user} does not have permission to create users in group {target_group}',
)

add_to_group = PermissionObject(
    model,
    'add_to_group',
    ['current_user', 'target_user', 'target_group'],
    'user {current_user} does not have permission to add user {target_user} to group {target_group}',
)

remove_from_group = PermissionObject(
    model,
    'remove_from_group',
    ['current_user', 'target_user', 'target_group'],
    'user {current_user} does not have permission to remove user {target_user} from group {target_group}',
)


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

    instance = PermissionAdder(model).visit(expr)

    db.session.commit()

    return instance


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
    print(query)
    return db.session.execute(query).all()

def any():
    return WildcardExpression()