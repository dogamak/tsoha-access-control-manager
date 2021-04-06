from tsoha.permissions.dsl.tokenize import Token, TokenKind
from tsoha.permissions.dsl.ast import ModelExpression, FilterExpression, JoinExpression, InstanceExpression, ParameterExpression, WildcardExpression

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


class UnexpectedToken(Exception):
    def __init__(self, token, message):
        self.token = token
        self.message = message
    
    def __str__(self):
        return f'Unexpected token: {self.message}, got: {self.token}'


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