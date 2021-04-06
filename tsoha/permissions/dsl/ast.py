class Expression:
    pass

class ModelExpression(Expression):
    def __init__(self, name):
        self.name = name
    
    def __repr__(self):
        return f'Model {{ name: "{self.name}" }}'
    
    def __str__(self):
        return self.name

class WildcardExpression(Expression):
    pass

class JoinExpression(Expression):
    def __init__(self, lhs, relationship):
        self.lhs = lhs
        self.relationship = relationship
    
    def __repr__(self):
        return f'Join {{ lhs: {repr(self.lhs)}, relationship: "{self.relationship}" }}'

    def __str__(self):
        return str(self.lhs) + '.' + self.relationship

class FilterExpression(Expression):
    def __init__(self, lhs, name, value):
        self.lhs = lhs
        self.name = name
        self.value = value
    
    def __repr__(self):
        return f'Filter {{ lhs: {repr(self.lhs)}, name: "{self.name}", value: {repr(self.value)} }}'
    
    def __str__(self):
        return f'{str(self.lhs)}#{self.name}({str(self.value)})'

class ParameterExpression(Expression):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f'Parameter {{ name: {repr(self.name)} }}'
    
    def __str__(self):
        return '$' + self.name

class InstanceExpression(Expression):
    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments
    
    def __repr__(self):
        arguments = ', '.join(map(repr, self.arguments))
        return f'Instance {{ name: {repr(self.name)}, arguments: [{arguments}] }}'
    
    def __str__(self):
        return f'{self.name}({", ".join(map(str, self.arguments))})'


class Visitor:
    def __init__(self, context=None):
        if context is None:
            context = {}

        self.context = context

    def visit_model_expression(self, expr):
        return expr
    
    def visit_join_expression(self, expr):
        return expr

    def visit_filter_expression(self, expr):
        return expr

    def visit_instance_expression(self, expr):
        return expr

    def visit_parameter_expression(self, expr):
        if expr.name in self.context:
            return self.visit(self.context[expr.name])
        
        raise Exception(f'no parameter named {repr(expr.name)} in scope')
    
    def visit_wildcard_expression(self, expr):
        return expr

    def visit_integer(self, value):
        return value

    def visit_text(self, value):
        return value

    def visit(self, expr):
        methods = [
            (ModelExpression,     self.visit_model_expression),
            (JoinExpression,      self.visit_join_expression),
            (FilterExpression,    self.visit_filter_expression),
            (WildcardExpression,  self.visit_wildcard_expression),
            (ParameterExpression, self.visit_parameter_expression),
            (InstanceExpression,  self.visit_instance_expression),
            (int,                 self.visit_integer),
            (str,                 self.visit_text),
        ]

        for expr_class, visitor in methods:
            if isinstance(expr, expr_class):
                return visitor(expr)

        raise Exception(f"Invalid expression: {repr(expr)}")


def into_ast_part(value):
    if isinstance(value, (str, int, Expression)):
        return value
    else:
        return value.into_ast()


def into_expression_ast(value, model=None):
    if isinstance(value, str):
        from tsoha.permissions.dsl.parse import Parser
        return Parser().parse(value)
    elif isinstance(value, Expression):
        return value
    elif model is not None and hasattr(value, '__permission_mapping__') and isinstance(getattr(value, '__permission_mapping__'), tuple):
        mapping = value.__permission_mapping__
        return model.get_object(mapping[0]).filter(mapping[1], getattr(value, mapping[2]))
    else:
        return value.into_ast()