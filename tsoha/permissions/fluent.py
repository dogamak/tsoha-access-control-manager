from tsoha.permissions.dsl.ast import into_ast_part, into_expression_ast
from tsoha.permissions.dsl import ast


class FluentExpression:
    def __init__(self, model):
        self.__model = model
    
    def __getattr__(self, name):
        if name == '__model':
            return self.__model

        if self.__model is None:
            return Relation(self, None, name, None)

        relationship = self.__model.get_relation(name)

        if relationship:
            return Relation(self, relationship.object_def, name, relationship)
    
    def filter(self, name, value):
        return Filter(self, self.__model, name, value)


class Filter(FluentExpression):
    def __init__(self, expr, model, name, value):
        super().__init__(model)
        self.expr = expr
        self.name = name
        self.value = value
    
    def into_ast(self):
        return ast.FilterExpression(into_ast_part(self.expr), self.name, into_ast_part(self.value))


class Relation(FluentExpression):
    def __init__(self, expr, model, name, definition):
        FluentExpression.__init__(self, model)
        self.expr = expr
        self.name = name
        self.definition = definition
    
    def into_ast(self):
        return ast.JoinExpression(into_ast_part(self.expr), self.name)


class Parameter(FluentExpression):
    def __init__(self, name):
        super().__init__(None)
        self.name = name
    
    def into_ast(self):
        return ast.ParameterExpression(self.name)


class PermissionConstructor:
    def __init__(self, model, name, arguments=None, error_message=None):
        self.model = model
        self.arguments = arguments
        self.name = name
        self.error_message = error_message

    def __call__(self, *values):
        if len(self.arguments) != len(values):
            raise Exception(f"permission '{self.name}' expects {len(self.arguments)} parameters, but {len(values)} given")

        return AnnotatedInstanceObject(
            self.name,
            map(lambda value: into_expression_ast(value, self.model), values),
            error_message=self.error_message,
        )

class InstanceObject:
    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments
    
    def into_ast(self):
        return ast.InstanceExpression(self.name, [ into_ast_part(arg) for arg in self.arguments ])


class AnnotatedInstanceObject(InstanceObject):
    def __init__(self, name, arguments, **kwargs):
        super().__init__(name, arguments)
        self.metadata = kwargs


def any():
    return ast.WildcardExpression()