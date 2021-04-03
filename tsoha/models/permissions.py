from tsoha import db
from tsoha.models import Base, User, Group, GroupMembership
from tsoha.permissions.expression import ObjectModel, QueryBuilder, ExpressionVisitor, Parser, tokenize, InstanceExpression

from sqlalchemy import select, join, exists, not_, and_
from sqlalchemy.orm import aliased


class Permission(Base):
    id = db.Column(db.String, primary_key=True)
    expr = db.Column(db.String, nullable=False)

class PermissionExpressionIndex(Base):
    id = db.Column(db.Integer, primary_key=True)
    object_type = db.Column(db.String)
    object_id = db.Column(db.Integer)
    parameter_number = db.Column(db.Integer)
    permission_id = db.Column(db.Integer, db.ForeignKey(Permission.id))
    permission = db.relationship(Permission)


class Role(Base):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=True)
    parameter_type = db.Column(db.String, nullable=True)


class RolePermissionTemplate(Base):
    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey(Role.id))
    template = db.Column(db.String)


class RoleInstance(Base):
    id = db.Column(db.Integer, primary_key=True)
    subject_type = db.Column(db.String)
    subject_id = db.Column(db.Integer)
    role_id = db.Column(db.Integer, db.ForeignKey(Role.id))
    parameter_id = db.Column(db.Integer, nullable=False)


model = ObjectModel()

secondary_join = lambda s:   lambda a, q: select([a]).select_from(join(q, s).join(a))
join_on_remote = lambda key: lambda a, q: select([a]).select_from(join(q, a, getattr(a, key) == q.id))
join_on_local  = lambda key: lambda a, q: select([a]).select_from(join(q, a, getattr(q, key) == a.id))

model.register_object(User) \
    .relation('groups', Group, secondary_join(GroupMembership)) \
    .relation('subordinates', User, join_on_remote('supervisor_id')) \
    .relation('supervisor', User, join_on_local('supervisor_id')) \
    .add_filter('id') \
    .add_filter('username')

model.register_object(Group) \
    .relation('members', User, secondary_join(GroupMembership)) \
    .relation('subgroups', Group, join_on_remote('parent_id')) \
    .relation('parent', Group, join_on_local('parent_id')) \
    .add_filter('id')


def extract_permission_arguments(ast):
    if not isinstance(ast, InstanceExpression):
        return []
    
    args = []

    for arg in ast.arguments:
        if isinstance(arg, (str, int)):
            continue

        if isinstance(arg, InstanceExpression):
            args += extract_permission_arguments(arg)
        else:
            args.append(arg)
    
    return args


class PermissionIdBuilder(ExpressionVisitor):
    def visit_instance_expression(self, name, arguments):
        parts = [name]

        for arg in arguments:
            parts += arg

        simplified = []

        for part in parts:
            if isinstance(part, int):
                if len(simplified) > 0 and isinstance(simplified[-1], int):
                    simplified[-1] += part
                    continue
        
            simplified.append(part)

        return simplified
    
    def visit_filter_expression(self, lhs, name, value):
        return [1]
    
    def visit_join_expression(self, lhs, name):
        return [1]

    def visit_model_expression(self, name):
        return [1]
    
    def visit_integer(self, value):
        return []
    
    def visit_text(self, value):
        return []
    
    @staticmethod
    def build(ast):
        return '#'.join(map(str, PermissionIdBuilder().visit(ast)))


def query_expr(expr):
    p = Parser()
    query, _ = QueryBuilder(model).build(p.parse(tokenize(expr)))
    return db.session.execute(query).all()

def validate_role(name, parameter, templates):
    return True

def into_instance_expr(value):
    if isinstance(value, str):
        return Parser.parse(value)
    elif isinstance(value, InstanceObject):
        return value.into_ast()
    elif isinstance(value, InstanceExpression):
        return value
    else:
        raise Exception("expected a string, an InstanceObject or an InstanceExpression")

def _add_permission(expr):
    expr = into_instance_expr(expr)

    instance_id = PermissionIdBuilder().build(expr)
    parametric_expressions = extract_permission_arguments(expr)

    perm = Permission(
        id=instance_id,
        expression=str(expr),
    )

    qb = QueryBuilder(model)

    for i, pexpr in enumerate(parametric_expressions):
        query, query_type = db.build(pexpr)

        for applicant_object in db.session.execute(query).all():
            db.session.add(PermissionExpressionIndex(
                permission=perm,
                index=i,
                object_type=query_type.schema.__tablename__,
                object_id=applicant_object.id,
            ))
    
    db.session.commit()


def _has_permission(expr):
    expr = into_instance_expr()

    instance_id = PermissionIdBuilder().build(expr)
    parametric_expressions = extract_permission_arguments(expr)

    alias = aliased(PermissionExpressionIndex)
    query = select(alias)

    for i, pexpr in parametric_expressions:
        joined = aliased(PermissionExpressionIndex)

        expr_type = get_expression_type(pexpr)

        if not expr_type.is_singular:
            yield Exception()

        query.join(joined, and_(
            alias.permission_id == joined.permission_id,
            joined.index == i,
            joined.object_type == ,
        ))


def add_permission(subject_expr, verb, object_expr):
    with db.session.begin():
        permission = Permission(
            object_expr=object_expr,
            subject_expr=subject_expr,
            verb=verb,
        )

        builder = QueryBuilder(model)

        subject_query, subject_model = builder.build(subject_expr)
        object_query, object_model = builder.build(objext_expr)

        subjects = db.session.execute(subject_query).all()
        objects = db.session.execute(object_query).all()

        for sub in subjects:
            entry = PermissionExpressionIndex(
                object_type=subject_model.schema.__tablename__,
                object_id=sub[0].id,
                is_subject=True,
                permission=permission,
            )

            db.session.add(entry)

        for obj in objects:
            entry = PermissionExpressionIndex(
                object_type=object_model.schema.__tablename__,
                object_id=obj[0].id,
                is_subject=False,
                permission=permission,
            )

            db.session.add(entry)


def has_permission(sub, verb, obj):
    primary = aliased(PermissionExpressionIndex)
    secondary = aliased(PermissionExpressionIndex)

    query = select(primary) \
        .filter(and_(
            primary.is_subject,
            primary.object_type == sub.__tablename__,
            primary.object_id == sub.id
        )) \
        .join(secondary, and_(
            not_(secondary.is_subject),
            secondary.object_type == obj.__tablename__,
            secondary.object_id == obj.id,
            secondary.permission_id == primary.permission_id
        )) \
        .join(Permission, and_(
            Permission.id == secondary.permission_id,
            Permission.verb == verb,
        )) \
        .exists() \
        .select()
    
    return db.session.execute(query).first()[0]

def manager(user, group):
    return [
        'add_permission($user, $group.members, write(group.doors->needs_pin))',
        add_permission(user, group.members, user.permissions),
    ]