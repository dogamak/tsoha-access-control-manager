class Expression:
    pass


def format_ast(value):
    if isinstance(value, str):
        value = value.replace('\\', '\\\\').replace('"', '\\"')
        return '"' + value + '"'
    else:
        return str(value)



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
        return format_ast(self.lhs) + '.' + self.relationship


class FilterExpression(Expression):
    def __init__(self, lhs, name, value):
        self.lhs = lhs
        self.name = name
        self.value = value
    
    def __repr__(self):
        return f'Filter {{ lhs: {repr(self.lhs)}, name: "{self.name}", value: {repr(self.value)} }}'
    
    def __str__(self):
        return f'{format_ast(self.lhs)}#{self.name}({format_ast(self.value)})'


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
        return f'{self.name}({", ".join(map(format_ast, self.arguments))})'


def into_ast_part(value):
    if isinstance(value, (str, int, Expression)):
        return value
    else:
        return value.into_ast()


def into_expression_ast(value, model=None):
    if isinstance(value, str):
        from tsoha.permissions.dsl.parse import Parser
        from tsoha.permissions.dsl.tokenize import tokenize
        return Parser().parse(tokenize(value))
    elif isinstance(value, Expression):
        return value
    elif model is not None and hasattr(value, '__permission_mapping__') and isinstance(getattr(value, '__permission_mapping__'), tuple):
        mapping = value.__permission_mapping__
        return model.get_object(mapping[0]).filter(mapping[1], getattr(value, mapping[2]))
    else:
        return value.into_ast()