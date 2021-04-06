import enum
import re

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