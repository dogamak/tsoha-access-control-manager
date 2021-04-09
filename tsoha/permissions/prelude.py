from tsoha.permissions.fluent import any
from tsoha.permissions.query import query_permission as query, query_expression as query_expr
from tsoha.permissions.insert import add_permission as add
from tsoha.models.permission import PermissionObjectModel

for name, obj in PermissionObjectModel.objects.items():
    globals()[name] = obj

for name, obj in PermissionObjectModel.permissions.items():
    globals()[name] = obj
