import enum
import sys
import collections
import re

from sqlalchemy import select, text, Column, Integer, Text, ForeignKey, join
from sqlalchemy.orm import aliased, relationship
from sqlalchemy.ext.declarative import declarative_base

class TokenKind(enum.Enum):
    FilterOperator     = 'filter'
    OpenParenthesis    = 'open'
    CloseParenthesis   = 'close'
    JoinOperator       = 'join'
    Integer            = 'int'
    Identifier         = 'segment'
    Text               = 'text'
    WildcardOperator   = '*'
    Parameter          = 'parameter'
    TypeAccessOperator = 'type_access'
    ArgumentListSeparator = 'argument_list_separator'


class PatternType(enum.Enum):
    RegEx   = 'regex'
    Literal = 'literal'


class TokenPattern:
    def __init__(self, kind, pattern, pattern_type=None, mapper=None, skip=False):
        self.kind = kind
        self.pattern = pattern
        self.pattern_type = pattern_type if pattern_type else PatternType.RegEx
        self.mapper = mapper if mapper else self.default_mapper
        self.skip = skip

        if self.pattern_type == PatternType.RegEx:
            self.pattern = re.compile(self.pattern)
    
    def match(self, input: str):
        raw = None
        value = None

        if self.pattern_type == PatternType.Literal:
            if input.startswith(self.pattern):
                raw = value = self.pattern
        elif self.pattern_type == PatternType.RegEx:
            value = self.pattern.match(input)
            raw = value.group(0) if value else None
        else:
            raise Exception("Unreachable code reached")

        if value:
            return self.create_token(raw, self.mapper(value))
        
        return None
    
    def default_mapper(self, value):
        if isinstance(value, str):
            return value
        
        elif isinstance(value, re.Match):
            if value.lastindex is not None:
                return value.group(value.lastindex)
            else:
                return value.group(0)
    
    def create_token(self, raw, value):
        return Token(self.kind, raw, value)


class Token:
    def __init__(self, kind, raw, value=None):
        self.kind = kind
        self.raw = raw
        self.value = value

    def __str__(self):
        return self.raw
    
    def __repr__(self):
        return f'<Token ({self.kind}) "{self.raw}">'
    
def unescape_string(match):
    return match.group(1).replace(r'\\"', r'"').replace(r'\\\\', r'\\')

TOKEN_PATTERNS = [
    TokenPattern(None, r'\s+', skip=True),
    TokenPattern(TokenKind.Text,                  r'"([^"\\]+|\\"|\\\\)*"', mapper=unescape_string),
    TokenPattern(TokenKind.Integer,               r'[0-9]+',                mapper=lambda m: int(m.group(0))),
    TokenPattern(TokenKind.Parameter,             r'\$([A-Za-z][A-Za-z0-9_]*)'),
    TokenPattern(TokenKind.Identifier,            r'[A-Za-z][A-Za-z0-9_]*'),
    TokenPattern(TokenKind.JoinOperator,          r'.',  PatternType.Literal),
    TokenPattern(TokenKind.FilterOperator,        r'#',  PatternType.Literal),
    TokenPattern(TokenKind.OpenParenthesis,       r'(',  PatternType.Literal),
    TokenPattern(TokenKind.CloseParenthesis,      r')',  PatternType.Literal),
    TokenPattern(TokenKind.WildcardOperator,      r'*',  PatternType.Literal),
    TokenPattern(TokenKind.TypeAccessOperator,    r'->', PatternType.Literal),
    TokenPattern(TokenKind.ArgumentListSeparator, r',',  PatternType.Literal),
]


def tokenize(expr):
    token = None

    while len(expr) > 0:
        for pattern in TOKEN_PATTERNS:
            token = pattern.match(expr)

            if token:
                if not pattern.skip:
                    yield token

                break
        else:
            raise Exception('Invalid input: ' + expr)
        
        expr = expr[len(token.raw):]


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

class UnexpectedToken(Exception):
    def __init__(self, token, message):
        self.token = token
        self.message = message
    
    def __str__(self):
        return f'Unexpected token: {self.message}, got: {self.token}'

# integer   := /[0-9]+/
# text      := /"[^"]*"/
# ident     := /[A-Za-z][A-Za-z0-9_]*/
# filter_op := "#"   
# join_op   := "*"
# type_op   := "->"
# open_par  := "("
# close_par := ")"
# wildcard_op := "*"

# model_expr    := <ident>
# join_expr     := <expr> <join_op> <ident>
# filter_expr   := <expr> <filter_op> <ident> <open_par> <expr> <close_par>
# argument_list := e | <expr> <argument_list_r>
# argument_list_r := e | "," <expr> <argument_list_r>
# instance_expr := <ident> <open_par> <argument_list> <close_par>
# expr          := <join_expr> | <filter_expr> | <integer> | <model_expr> | <text> | <instance_expr>

# expr       := <text> | <integer> | <parameter> | <wildcard_op> | <expr_r>
# expr2      := <ident> <expr_r>
# expr_r     := <type_op> <ident> <expr_opt>
#             | <filter_op> <ident> <open_par> <expr> <close_par> <expr_opr>
#             | <join_op> <ident> <expr_opt>
# expr_opt   := e | <expr_r>


class Parser:
    def __init__(self):
        self.tokens = None
        self.lookahead = None
    
    def parse(self, tokens):
        self.tokens = tokens
        self.lookahead = None

        return self.parse_expr()
    
    def next_token(self):
        if self.lookahead is not None:
            token = self.lookahead
            self.lookahead = None
            return token

        return next(self.tokens)
    
    def peek_token(self):
        if self.lookahead is None:
            self.lookahead = self.next_token()
        
        return self.lookahead
    
    def expect_token(self, kind, token=None):
        if token is None:
            token = self.next_token()
        
        if token.kind != kind:
            raise UnexpectedToken(token, f'expected {kind}')

        return token
    
    def check_token(self, *kinds):
        token = self.peek_token()

        if token.kind in kinds:
            return self.next_token()
        else:
            return None
    
    def parse_identifier(self):
        return self.expect_token(TokenKind.Identifier).value

    def parse_expr(self):
        if token := self.check_token(TokenKind.Text, TokenKind.Integer):
            return token.value
        
        if token := self.check_token(TokenKind.Parameter):
            return ParameterExpression(token.value)
        
        if token := self.check_token(TokenKind.WildcardOperator):
            return WildcardExpression()
        
        token = self.expect_token(TokenKind.Identifier)

        if self.peek_token().kind == TokenKind.OpenParenthesis:
            return self.parse_instance_rest(token.value)

        lhs = ModelExpression(token.value)
        return self.parse_expr_opt(lhs)
    
    def parse_instance_rest(self, name):
        self.expect_token(TokenKind.OpenParenthesis)
        arguments = self.parse_argument_list()
        return InstanceExpression(name, arguments)
    
    def parse_argument_list(self):
        token = self.peek_token()

        if token.kind == TokenKind.CloseParenthesis:
            return []
        
        expr = self.parse_expr()

        return [ expr ] + self.parse_argument_list_rest()
    
    def parse_argument_list_rest(self):
        if self.check_token(TokenKind.CloseParenthesis):
            return []
        elif self.check_token(TokenKind.ArgumentListSeparator):
            expr = self.parse_expr()
            return [expr] + self.parse_argument_list_rest()
        else:
            raise Exception("Expected an expression")
    
    def parse_expr_rest(self, lhs):
        if self.check_token(TokenKind.JoinOperator):
            return self.parse_join_op(lhs)
        
        elif self.check_token(TokenKind.FilterOperator):
            return self.parse_filter_op(lhs)
        
        else:
            raise UnexpectedToken(self.peek_token(), 'expected either a filter or a join operator')

    def parse_expr_opt(self, lhs):
        try:
            self.peek_token()
            return self.parse_expr_rest(lhs)
        except StopIteration:
            return lhs
        except UnexpectedToken:
            return lhs
    
    def parse_filter_op(self, lhs):
        name = self.parse_identifier()
        self.expect_token(TokenKind.OpenParenthesis)
        value = self.parse_expr()
        self.expect_token(TokenKind.CloseParenthesis)

        expr = FilterExpression(lhs, name, value)
        return self.parse_expr_opt(expr)
    
    def parse_join_op(self, lhs):
        name = self.parse_identifier()
        expr = JoinExpression(lhs, name)
        return self.parse_expr_opt(expr)


class ExpressionVisitor:
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


class ExpressionObj:
    def __init__(self, model):
        self.__model = model
    
    def __getattr__(self, name):
        if self.__model is None:
            return Relation(self, None, name, None)

        relationship = self.__model.get_relation(name)

        if relationship:
            return Relation(self, self.__model, name, relationship)
    
    def filter(self, name, value):
        return FilterObj(self, self.__model, name, value)


def into_ast_part(value):
    if isinstance(value, (str, int, Expression)):
        return value
    else:
        return value.into_ast()


def into_expression_ast(value, model=None):
    if isinstance(value, str):
        return Parser().parse(value)
    elif isinstance(value, Expression):
        return value
    elif model is not None and hasattr(value, '__permission_mapping__') and isinstance(getattr(value, '__permission_mapping__'), tuple):
        mapping = value.__permission_mapping__
        return model.get_object(mapping[0]).filter(mapping[1], getattr(value, mapping[2]))
    else:
        return value.into_ast()


class FilterObj(ExpressionObj):
    def __init__(self, expr, model, name, value):
        super().__init__(model)
        self.expr = expr
        self.name = name
        self.value = value
    
    def into_ast(self):
        return FilterExpression(into_ast_part(self.expr), self.name, into_ast_part(self.value))


class Relation(ExpressionObj):
    def __init__(self, expr, model, name, definition):
        super().__init__(model)
        self.expr = expr
        self.name = name
        self.definition = definition
    
    def into_ast(self):
        return JoinExpression(into_ast_part(self.expr), self.name)

class Parameter(ExpressionObj):
    def __init__(self, name):
        super().__init__(None)
        self.name = name
    
    def into_ast(self):
        return ParameterExpression(self.name)


class ObjectDef(ExpressionObj):
    def __init__(self, model, schema):
        print(self)
        super().__init__(self)
        self.schema = schema
        self.relations = dict()
        self.filters = dict()
        self.model = model
    
    def into_ast(self):
        return ModelExpression(self.schema.__tablename__)

    def relation(self, relation, *args, **kwargs):
        self.relations[relation] = RelationDef(self.model, relation, *args, **kwargs)
        return self
    
    def add_filter(self, name, *args, **kwargs):
        self.filters[name] = FilterDef(self.model, name, *args, **kwargs)
        return self

    def get_filter(self, name):
        return self.filters[name]
    
    def get_relation(self, relation):
        return self.relations.get(relation)
    
    def get_primary_key(self):
        return next(filter(lambda f: f.is_primary_key, self.filters.values()))


class RelationDef:
    def __init__(self, model, name, obj, is_singular=False, joiner=None):
        self.model = model
        self.name = name
        self._object_def = obj
        self.is_singular = is_singular
        self.joiner = joiner
    
    @property
    def object_def(self):
        if isinstance(self._object_def, str):
            self._object_def = self.model.get_object(self._object_def)
        
        return self._object_def
    
    def join(self, a, b):
        if self.joiner:
            return self.joiner(a, b)
        else:
            return select(a).select_from(join(a, b))


class FilterDef:
    def __init__(self, model, name, unique=None, primary_key=None):
        self.model = model
        self.name = name
        self.is_primary_key = False
        self.is_unique = False

        if primary_key:
            self.is_primary_key = True
            self.is_unique = True

            if unique is not None and unique is not True:
                raise Exception("primary keys are always unique by definition")
        
        if unique:
            self.is_unique = True


class PermissionObject:
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
        return InstanceExpression(self.name, [ into_ast_part(arg) for arg in self.arguments ])


class AnnotatedInstanceObject(InstanceObject):
    def __init__(self, name, arguments, **kwargs):
        super().__init__(name, arguments)
        self.metadata = kwargs


class ObjectModel:
    def __init__(self):
        self.objects = {}
    
    def register_object(self, name, obj):
        d = ObjectDef(self, obj)
        self.objects[name] = d
        return d
    
    def get_object(self, name):
        return self.objects[name]


class ExpressionType:
    pass


class EvaluatedExpression:
    def __init__(self, object_def=None, query=None, value=None, is_singular=None, is_literal=False, is_wildcard=False):
        self.object_def = object_def
        self.query = query
        self.is_singular = is_singular if is_singular is not None else is_literal
        self.is_literal = is_literal
        self.value = value
        self.is_wildcard = is_wildcard
        self.known_values = {}
    
    @property
    def primary_key(self):
        if not self.is_singular:
            raise Exception()
        
        filter_def = self.object_def.get_primary_key()

        if filter_def.name in self.known_values:
            return self.known_values[filter_def.name]
        
        raise Exception('primary key could not be inferred for the expression')

    @property
    def schema(self):
        return self.object_def.schema


"""
def into_ast(value):
    if isinstance(value, Expression):
        return value
    elif isinstance(value, ExpressionObj):
        return value.into_ast()
    elif isinstance(value, str):
        return Parser().parse(value)
    else:
        raise Exception("expected a string, an expression AST or an expression object")
"""


class ExpressionInterpreter(ExpressionVisitor):
    def __init__(self, model):
        self.model = model
    
    def visit_instance_expression(self, expr): 
        pass

    def visit_model_expression(self, expr):
        obj_def = self.model.get_object(expr.name)
        query = select([obj_def.schema])

        return EvaluatedExpression(object_def=obj_def, query=query)
    
    def visit_filter_expression(self, expr):
        lhs = self.visit(expr.lhs)
        value = self.visit(expr.value)

        filter_def = lhs.object_def.get_filter(expr.name)

        if filter_def is None:
            raise Exception(f"no filter '{expr.name}' defined for object '{lhs.schema.__tablename__}'")
        
        a = aliased(lhs.schema, alias=lhs.query.subquery())

        if value.is_literal:
            result = select(a).where(getattr(a, expr.name) == value.value)
        elif value.is_singular:
            result = select(a).where(getattr(a, expr.name) == value.query)
        else:
            result = select(a).where(getattr(a, expr.name).in_(value.query))

        if filter_def.is_unique:
            lhs.is_singular = True

            if value.is_literal:
                lhs.known_values[expr.name] = value.value
        
        lhs.query = result
        
        return lhs
    
    def visit_join_expression(self, expr):
        lhs = self.visit(expr.lhs)

        relation_def = lhs.object_def.get_relation(expr.name) 

        if relation_def is None:
            raise Exception(f"no relation '{expr.name}' defined for object '{lhs.schema.__tablename__}'")
        
        query = relation_def.join(relation_def.object_def.schema, aliased(lhs.schema, alias=lhs.query.subquery()))

        return EvaluatedExpression(
            object_def=relation_def.object_def,
            is_singular=relation_def.is_singular and lhs.is_singular,
            query=query,
        )
    
    def visit_wildcard_expression(self, _expr):
        return EvaluatedExpression(is_wildcard=True)
    
    def visit_integer(self, value):
        return EvaluatedExpression(is_literal=True, value=value)
    
    def visit_text(self, value):
        return EvaluatedExpression(is_literal=True, value=value)