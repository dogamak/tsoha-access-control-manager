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

# model_expr    := <ident>
# join_expr     := <expr> <join_op> <ident>
# filter_expr   := <expr> <filter_op> <ident> <open_par> <expr> <close_par>
# argument_list := e | <expr> <argument_list_r>
# argument_list_r := e | "," <expr> <argument_list_r>
# instance_expr := <ident> <open_par> <argument_list> <close_par>
# expr          := <join_expr> | <filter_expr> | <integer> | <model_expr> | <text> | <instance_expr>

# expr       := <text> | <integer> | <parameter> | <expr_r>
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
    
    def parse_identifier(self):
        return self.expect_token(TokenKind.Identifier).value

    def parse_expr(self):
        token = self.peek_token()

        if token.kind in (TokenKind.Text, TokenKind.Integer):
            self.next_token()
            return token.value
        
        if token.kind == TokenKind.Parameter:
            self.next_token()
            return ParameterExpression(token.value)
        
        self.expect_token(TokenKind.Identifier)

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
        token = self.peek_token()

        if token.kind == TokenKind.CloseParenthesis:
            self.next_token()
            return []
        elif token.kind == TokenKind.ArgumentListSeparator:
            self.next_token()
            expr = self.parse_expr()
            return [expr] + self.parse_argument_list_rest()
        else:
            raise Exception("Expected an expression")
    
    def parse_expr_rest(self, lhs):
        token = self.peek_token()

        if token.kind == TokenKind.JoinOperator:
            self.next_token()
            return self.parse_join_op(lhs)
        
        elif token.kind == TokenKind.FilterOperator:
            self.next_token()
            return self.parse_filter_op(lhs)
        
        else:
            raise UnexpectedToken(token, 'expected either a filter or a join operator')

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

    def visit_model_expression(self, name):
        pass
    
    def visit_join_expression(self, lhs, name):
        pass

    def visit_filter_expression(self, lhs, name, value):
        pass

    def visit_instance_expression(self, name, args):
        pass

    def visit_parameter_expression(self, name):
        if name in self.context:
            return self.visit(self.context[name])
        
        raise Exception(f'no parameter named {repr(name)} in scope')

    def visit_integer(self, value):
        return value

    def visit_text(self, value):
        return value

    def visit(self, expr):
        if isinstance(expr, ModelExpression):
            return self.visit_model_expression(expr.name)
        elif isinstance(expr, JoinExpression):
            return self.visit_join_expression(self.visit(expr.lhs), expr.relationship)
        elif isinstance(expr, FilterExpression):
            return self.visit_filter_expression(self.visit(expr.lhs), expr.name, self.visit(expr.value))
        elif isinstance(expr, ParameterExpression):
            return self.visit_parameter_expression(expr.name)
        elif isinstance(expr, InstanceExpression):
            return self.visit_instance_expression(expr.name, [
                self.visit(arg) for arg in expr.arguments
            ])
        elif isinstance(expr, int):
            return self.visit_integer(expr)
        elif isinstance(expr, str):
            return self.visit_text(expr)
        else:
            raise Exception(f"Invalid experession: {repr(expr)}")


class QueryBuilder(ExpressionVisitor):
    def __init__(self, model, context=None):
        super().__init__(context)
        self.model = model

    def visit_model_expression(self, name):
        obj = self.model.get_object(name)
        return select(obj.schema), obj
    
    def visit_join_expression(self, lhs, name):
        lhs, lhs_type = lhs
        value_type, joiner = lhs_type.get_relation(name)
        value = joiner(value_type.schema, aliased(lhs_type.schema, alias=lhs))
        return value, value_type
    
    def visit_filter_expression(self, lhs, name, value):
        lhs, lhs_type = lhs
        value, value_type = value

        a = aliased(lhs_type.schema, alias=lhs.subquery())

        if value_type in (str, int):
            result = select(a).where(getattr(a, name) == value)
        else:
            result = select(a).where(getattr(a, name).in_(value))

        return result, lhs_type
    
    def visit_integer(self, value):
        return value, int
    
    def visit_text(self, value):
        return value, str
    
    def build(self, ast):
        query, _ = self.visit(ast)
        return query


"""class QueryValidator(ExpressionVisitor):
    def __init__(self, model):
        self.model = model

    def visit_model_expression(self, name):
        return self.model.get_object(name).schema
    
    def visit_join_expression(self, lhs, name):
        value_type, _joiner = lhs_type.get_relation(name)
        return getattr(value_type, name)
    
    def visit_filter_expression(self, lhs, name, value):
        return lhs

    def validate(self, ast):
        try:
            self.visit(ast)
        except Exception:
            return False
        
        return True


class NewQueryBuilder:
    def __init__(self, model):
        self.model = model
    
    def build(self, ast):
        return self.visit_expression(ast)
    
    def visit_expression(self, ast):
        if isinstance(ast, ModelExpression):
            return self.visit_model_expr(ast)
        elif isinstance(ast, JoinExpression):
            return self.visit_join_expr(ast)
        elif isinstance(ast, FilterExpression):
            return self.visit_filter_expr(ast)
        elif isinstance(ast, (int, str)):
            return ast, type(ast)
        else:
            raise Exception(f"Invalid experession: {repr(ast)}")
    
    def visit_model_expr(self, expr):
        obj = self.model.get_object(expr.name)
        return select(obj.schema), obj
    
    def visit_join_expr(self, expr):
        lhs, lhs_type = self.visit_expression(expr.lhs)
        value_type, joiner = lhs_type.get_relation(expr.relationship)
        value = joiner(value_type.schema, aliased(lhs_type.schema, alias=lhs))
        return value, value_type
    
    def visit_filter_expr(self, expr):
        lhs, lhs_type = self.visit_expression(expr.lhs)
        value, value_type = self.visit_expression(expr.value)

        a = aliased(lhs_type.schema, alias=lhs.subquery())

        if value_type in (str, int):
            result = select(a).where(getattr(a, expr.name) == value)
        else:
            result = select(a).where(getattr(a, expr.name).in_(value))

        return result, lhs_type


class QueryBuilder:
    def __init__(self, model, expression, template=None):
        self.model = model
        print(list(tokenize(expression)))
        self.tokenizer = tokenize(expression)

        self.lookback = None

        self.template = template
        self.template_tokenizer = None
        self.template_tokens = []
        self.template_tokenized = False
    
    def assert_token(self, kind):
        token = self.next_token()

        if token.kind == kind:
            return token.value
        else:
            raise Exception(f'Expected an identifier, got {token.kind}')
    
    def next_token(self):
        def inner():
            if self.lookback:
                token = self.lookback
                self.lookback = None
                return token

            if self.template_tokenizer:
                try:
                    token = next(self.template_tokenizer)

                    if not self.template_tokenized:
                        self.template_tokens.append(token)
                    
                    return token
                except StopIteration:
                    self.template_tokenizer = None
                    self.template_tokenized = True
            
            return next(self.tokenizer)
        
        token = inner()
        print(f'Token: {token}')
        return token
    
    def peek_token(self):
        if self.lookback:
            return self.lookback
        else:
            self.lookback = self.next_token()
            return self.lookback
    
    def insert_template(self):
        if not self.template:
            return

        if self.template_tokenizer:
            return
        
        if self.peek_token().kind != TokenKind.TemplatePlaceholder:
            return
        
        self.assert_token(TokenKind.TemplatePlaceholder)

        if self.template_tokenized:
            self.template_tokenizer = iter(self.template_tokens)
        else:
            self.template_tokenizer = tokenize(self.template)

    
    def validate(self):
        self.insert_template()
        root_obj_name = self.assert_token(TokenKind.Identifier)
        obj = self.model.get_object(root_obj_name)

        while True:
            try:
                op = self.next_token()
            except StopIteration:
                return True

            if op.kind == TokenKind.FilterOperator:
                field = self.assert_token(TokenKind.Identifier)
                self.assert_token(TokenKind.OpenParenthesis)
                _value = self.next_token()
                self.assert_token(TokenKind.CloseParenthesis)

                f = obj.get_filter(field)

                if not f:
                    raise Exception(f'Invalid filter "{field}" for object "{obj.schema.__tablename__}"')
            
            elif op.kind == TokenKind.SegmentSeparator:
                child = self.assert_token(TokenKind.Identifier)

                relation = obj.get_relation(child)

                if not relation:
                    raise Exception(f'Invalid relation "{child}" for object "{obj.schema.__tablename__}"')
                
                child_model, _joiner = relation
                obj = child_model

    
    def build(self):
        root_obj_name = self.assert_token(TokenKind.Identifier)

        obj = self.model.get_object(root_obj_name)
        query = select([obj.schema])

        while True:
            try:
                op = self.next_token()
            except StopIteration:
                return query, obj

            if op.kind == TokenKind.FilterOperator:
                field = self.assert_token(TokenKind.Identifier)
                self.assert_token(TokenKind.OpenParenthesis)
                value = self.next_token()
                self.assert_token(TokenKind.CloseParenthesis)

                f = obj.get_filter(field)

                if not f:
                    raise Exception(f'Invalid filter "{field}" for object "{obj.schema.__tablename__}"')

                subq = aliased(obj.schema, alias=query.subquery())
                query = select([subq]).where(getattr(subq, field) == value.value)
            
            elif op.kind == TokenKind.SegmentSeparator:
                child = self.assert_token(TokenKind.Identifier)

                relation = obj.get_relation(child)

                if not relation:
                    raise Exception(f'Invalid relation "{child}" for object "{obj.schema.__tablename__}"')
                
                child_model, joiner = relation

                a = child_model.schema
                q = aliased(obj.schema, alias=query.subquery())

                query = joiner(a, q)
                obj = child_model
        
        return query, obj"""

Model = declarative_base()


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


def into_ast(value):
    if isinstance(value, (str, int)):
        return value
    else:
        return value.into_ast()


class FilterObj(ExpressionObj):
    def __init__(self, expr, model, name, value):
        super().__init__(model)
        self.expr = expr
        self.name = name
        self.value = value
    
    def into_ast(self):
        return FilterExpression(into_ast(self.expr), self.name, into_ast(self.value))


class Relation(ExpressionObj):
    def __init__(self, expr, model, name, definition):
        super().__init__(model)
        self.expr = expr
        self.name = name
        self.definition = definition
    
    def into_ast(self):
        return JoinExpression(into_ast(self.expr), self.name)

class Parameter(ExpressionObj):
    def __init__(self, name):
        super().__init__(None)
        self.name = name
    
    def into_ast(self):
        return ParameterExpression(self.name)


import inspect

def role(func):
    args = [ Parameter(name) for name in inspect.signature(func).parameters ]
    return func(*args)


class ObjectDef(ExpressionObj):
    def __init__(self, model, schema):
        print(self)
        super().__init__(self)
        self.schema = schema
        self.relations = {}
        self.filters = []
        self.model = model
    
    def into_ast(self):
        return ModelExpression(self.schema.__tablename__)

    def relation(self, relation, obj, joiner=None):
        if joiner is None:
            joiner = lambda a, q: select([a]).select_from(join(a, q))

        self.relations[relation] = (obj, joiner)
        return self
    
    def add_filter(self, filter):
        self.filters.append(filter)
        return self

    def get_filter(self, filter):
        return filter in self.filters
    
    def get_relation(self, relation):
        relation = self.relations.get(relation)

        if not relation:
            return None
        
        schema, joiner = relation
        return self.model.get_object(schema.__tablename__), joiner


class PermissionFunction:
    def __init__(self, name, arguments=[]):
        self.arguments = arguments
        self.name = name

    def __call__(self, *values):
        return InstanceObject(self.name, values)


class InstanceObject:
    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments
    
    def into_ast(self):
        return InstanceExpression(self.name, [ into_ast(arg) for arg in self.arguments ])


class ObjectModel:
    def __init__(self):
        self.objects = {}
    
    def register_object(self, obj):
        d = ObjectDef(self, obj)
        self.objects[obj.__tablename__] = d
        return d
    
    def get_object(self, name):
        return self.objects[name]


class ExpressionType:
    pass

class SelectionExpression(ExpressionType):
    def __init__(self, obj, singular=False):
        self.object = obj
        self.is_singular = singular

    def __repr__(self):
        if self.is_singular:
            return f'<Type: Selection (Singular)>'
        else:
            return f'<Type: Selection>'

class InstanceExpressionType(ExpressionType):
    def __init__(self, name, argument_count):
        self.name = name
        self.argument_count = argument_count
    
    def __repr__(self):
        return f'<Type: Instance (name={repr(self.name)}, arguments={self.argument_count})>'


class ExpressionTypeChecker(ExpressionVisitor):
    def __init__(self, model):
        self.model = model
    
    def visit_instance_expression(self, name, arguments):
        return InstanceExpressionType(name, len(arguments))
    
    def visit_model_expression(self, name):
        obj = self.model.get_object(name)
        return SelectionExpression(obj)
    
    def visit_join_expression(self, lhs, name):
        value_type, _ = lhs.get_relation(name)
        return SelectionExpression(value_type)
    
    def visit_filter_expression(self, lhs, name, value):
        filter_def = lhs.get_filter(name)

        if filter_def.is_unique:
            return SelectionExpression(lhs.model, singular=True)
        else:
            return lhs
    
    @staticmethod
    def from_expr(model, expr):
        return ExpressionTypeChecker(model).visit(expr)


def test():
    from tsoha.models.permissions import model
    from tsoha import db

    p = Parser()
    t = p.parse('group#id(1)')

    tp = Parser(template=t)
    e = tp.parse('$.members')

    b = NewQueryBuilder(model)
    query, kind = b.build(e)

    print(query)
    print(kind)

    print(db.session.execute(query).all())