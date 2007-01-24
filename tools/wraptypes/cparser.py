#!/usr/bin/env python

'''Parse a C source file.

Unlike the ctypes-gen wrapper or GCC-XML, preprocessing is done in the same
pass as parsing, and are included in the grammar.  Macros are expanded as
usual (but not macro functions).

The lexicon is complete, however the grammar is only currently equipped for
declarations (function implementations will cause a parse error).  Structs, 
enums, and initializer values are also not handled yet and will cause a parse
error.

Preprocessing behaviour is not like an ordinary compiler:

  * Preprocessor declarations can occur only between declarations (i.e., not
    in the middle of one).  
  * Macros are expanded as usual (except for function macros).
  * #define and #undef behave as usual.
  * #ifdef, #ifndef, #if and #else are ignored, with the exception of 
    #ifdef __cplusplus, whose contents are skipped.  (This handling should be
    improved TODO).

To use, subclass CParser and override its handle_* methods.  Then instantiate
the class with a string to parse.

Derived from ANSI C grammar:
  * Lexicon: http://www.lysator.liu.se/c/ANSI-C-grammar-l.html
  * Grammar: http://www.lysator.liu.se/c/ANSI-C-grammar-y.html

Reference is C99:
  * http://www.open-std.org/JTC1/SC22/WG14/www/docs/n1124.pdf

'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import operator
import re
import sys

# lex and yacc are from PLY (http://www.dabeaz.com/ply) but have been modified
# for this tool.  See README in this directory.
import lex
from lex import TOKEN
import yacc

__all__ = ['CParser', 'DebugCParser',
           'Declaration', 'Pointer', 'Declarator', 'Array', 'Parameter',
           'Type']

states = (
    ('SKIPTEXT', 'exclusive'),  # in skipped if/else block
    ('PPBEGIN', 'exclusive'),   # after hash, before keyword
    ('PP', 'exclusive'),        # in pp line after keyword, before newline
)

tokens = (
    'PP_HASH', 'PP_NEWLINE',

    'PP_IF', 'PP_IFDEF', 'PP_IFNDEF', 'PP_ELIF', 'PP_ELSE',
    'PP_ENDIF', 'PP_INCLUDE', 'PP_DEFINE', 'PP_UNDEF', 'PP_LINE',
    'PP_ERROR', 'PP_PRAGMA', 'PP_LPAREN', 
    
    'PP_HEADER_NAME', 'PP_NUMBER',

    'IDENTIFIER', 'CONSTANT', 'CHARACTER_CONSTANT', 'STRING_LITERAL', 'SIZEOF',

    'PTR_OP', 'INC_OP', 'DEC_OP', 'LEFT_OP', 'RIGHT_OP', 'LE_OP', 'GE_OP',
    'EQ_OP', 'NE_OP', 'AND_OP', 'OR_OP', 'MUL_ASSIGN', 'DIV_ASSIGN',
    'MOD_ASSIGN', 'ADD_ASSIGN', 'SUB_ASSIGN', 'LEFT_ASSIGN', 'RIGHT_ASSIGN',
    'AND_ASSIGN', 'XOR_ASSIGN', 'OR_ASSIGN',  'HASH_HASH', 'PERIOD',
    'TYPE_NAME', 
    
    'TYPEDEF', 'EXTERN', 'STATIC', 'AUTO', 'REGISTER', 
    'CHAR', 'SHORT', 'INT', 'LONG', 'SIGNED', 'UNSIGNED', 'FLOAT', 'DOUBLE',
    'CONST', 'VOLATILE', 'VOID',
    'STRUCT', 'UNION', 'ENUM', 'ELLIPSIS',

    'CASE', 'DEFAULT', 'IF', 'ELSE', 'SWITCH', 'WHILE', 'DO', 'FOR', 'GOTO',
    'CONTINUE', 'BREAK', 'RETURN'
)

keywords = [
    'auto', 'break', 'case', 'char', 'const', 'continue', 'default', 'do',
    'double', 'else', 'enum', 'extern', 'float', 'for', 'goto', 'if', 'int',
    'long', 'register', 'return', 'short', 'signed', 'sizeof', 'static',
    'struct', 'switch', 'typedef', 'union', 'unsigned', 'void', 'volatile',
    'while'
]

pp_keywords = [
    'if', 'ifdef', 'ifndef', 'elif', 'else', 'endif', 'include', 'define',
    'undef', 'line', 'error', 'pragma'
]

subs = {
    'D': '[0-9]',
    'L': '[a-zA-Z_]',
    'H': '[a-fA-F0-9]',
    'E': '[Ee][+-]?{D}+',
    'FS': '[FflL]',
    'IS': '[uUlL]*',
}
# Helper: substitute {foo} with subs[foo] in string (makes regexes more lexy)
sub_pattern = re.compile('{([^}]*)}')
def sub_repl_match(m):
    return subs[m.groups()[0]]
def sub(s):
    return sub_pattern.sub(sub_repl_match, s)

CHARACTER_CONSTANT = sub(r"L?'(\\.|[^\\'])+'")
FLOAT_CONSTANT = sub(r'({D}*\\.{D}+({E})?|{D}+\\.{D}*({E})?|{D}+{E}){FS}?')
STRING_LITERAL = sub(r'L?"(\\.|[^\\"])*"')

# --------------------------------------------------------------------------
# Token declarations
# --------------------------------------------------------------------------

punctuators = {
    # value: (regex, type)
    r'...': (r'\.\.\.', 'ELLIPSIS'),
    r'>>=': (r'>>=', 'RIGHT_ASSIGN'),
    r'<<=': (r'<<=', 'LEFT_ASSIGN'),
    r'+=': (r'\+=', 'ADD_ASSIGN'),
    r'-=': (r'-=', 'SUB_ASSIGN'),
    r'*=': (r'\*=', 'MUL_ASSIGN'),
    r'/=': (r'/=', 'DIV_ASSIGN'),
    r'%=': (r'%=', 'MOD_ASSIGN'),
    r'&=': (r'&=', 'AND_ASSIGN'),
    r'^=': (r'\^=', 'XOR_ASSIGN'),
    r'|=': (r'\|=', 'OR_ASSIGN'),
    r'>>': (r'>>', 'RIGHT_OP'),
    r'<<': (r'<<', 'LEFT_OP'),
    r'++': (r'\+\+', 'INC_OP'),
    r'--': (r'--', 'DEC_OP'),
    r'->': (r'->', 'PTR_OP'),
    r'&&': (r'&&', 'AND_OP'),
    r'||': (r'\|\|', 'OR_OP'),
    r'<=': (r'<=', 'LE_OP'),
    r'>=': (r'>=', 'GE_OP'),
    r'==': (r'==', 'EQ_OP'),
    r'!=': (r'!=', 'NE_OP'),
    r'<:': (r'<:', '['),
    r':>': (r':>', ']'),
    r'<%': (r'<%', '{'),
    r'%>': (r'%>', '}'),
    r'%:%:': (r'%:%:', 'HASH_HASH'),
    r';': (r';', ';'),
    r'{': (r'{', '{'),
    r'}': (r'}', '}'),
    r',': (r',', ','),
    r':': (r':', ':'),
    r'=': (r'=', '='),
    r'(': (r'\(', '('),
    r')': (r'\)', ')'),
    r'[': (r'\[', '['),
    r']': (r']', ']'),
    r'.': (r'\.', 'PERIOD'),
    r'&': (r'&', '&'),
    r'!': (r'!', '!'),
    r'~': (r'~', '~'),
    r'-': (r'-', '-'),
    r'+': (r'\+', '+'),
    r'*': (r'\*', '*'),
    r'/': (r'/', '/'),
    r'%': (r'%', '%'),
    r'<': (r'<', '<'),
    r'>': (r'>', '>'),
    r'^': (r'\^', '^'),
    r'|': (r'\|', '|'),
    r'?': (r'\?', '?'),
}

def punctuator_regex(punctuators):
    punctuator_regexes = [v[0] for v in punctuators.values()]
    punctuator_regexes.sort(lambda a, b: -cmp(len(a), len(b)))
    return '(%s)' % '|'.join(punctuator_regexes)

# C /* comments */.  Copied from the ylex.py example in PLY: it's not 100%
# correct for ANSI C, but close enough for anything that's not crazy.
def t_ANY_ccomment(t):
    r'/\*(.|\n)*?\*/'
    t.lexer.lineno += t.value.count('\n')

# --------------------------------------------------------------------------
# PPBEGIN state
# --------------------------------------------------------------------------

# Any token will switch state from PPBEGIN to PP (except newline).

def t_PPBEGIN_header_name(t):
    r'<[^\n>]+>'
    # Is also r'"[^\n"]"', but handled in STRING_LITERAL instead.
    t.lexer.begin('PP')
    t.type = 'PP_HEADER_NAME'
    return t

@TOKEN(sub('{L}({L}|{D})*'))
def t_PPBEGIN_identifier(t):
    t.lexer.begin('PP')
    if t.value in pp_keywords:
        t.type = 'PP_%s' % t.value.upper()
        return t
    else:
        t.type = 'IDENTIFIER'
        return t

# missing: universal-character-constant
@TOKEN(sub(r'({D}|\.{D})({D}|{L}|e[+-]|E[+-]|p[+-]|P[+-]|\.)*'))
def t_PPBEGIN_pp_number(t):
    t.lexer.begin('PP')
    t.type = 'PP_NUMBER'
    return t
    
@TOKEN(CHARACTER_CONSTANT)
def t_PPBEGIN_character_constant(t):
    t.lexer.begin('PP')
    t.type = 'CHARACTER_CONSTANT'
    return t

@TOKEN(STRING_LITERAL)
def t_PPBEGIN_string_literal(t):
    t.lexer.begin('PP')
    t.type = 'STRING_LITERAL'

def t_PPBEGIN_newline(t):
    r'\n'
    t.lexer.pop_state()
    t.lexer.lineno += 1
    t.type = 'PP_NEWLINE'
    return t

def t_PPBEGIN_error(t):
    t.lexer.begin('PP')
    t.lexer.skip(1)

t_PPBEGIN_ignore = ' \t\v\f'

# --------------------------------------------------------------------------
# PP state
# --------------------------------------------------------------------------

# These punctuators are handled specially
pp_punctuators = punctuators.copy()
del pp_punctuators[r'(']

# Hash can be a punctuator now
pp_punctuators[r'#'] = (r'\#', '#')

@TOKEN(punctuator_regex(pp_punctuators))
def t_PP_punctuator(t):
    t.lexer.begin('PP')
    t.type = pp_punctuators[t.value][1]
    return t


def t_PP_header_name(t):
    r'<[^\n>]+>'
    # Is also r'"[^\n"]"', but handled in STRING_LITERAL instead.
    t.type = 'PP_HEADER_NAME'
    return t

@TOKEN(sub('{L}({L}|{D})*'))
def t_PP_identifier(t):
    # 'defined' is a reserved word in PP state, but grammar is simpler if it's
    # left as an identifier and sorted out somewhere else.
    t.type = 'IDENTIFIER'
    return t

# missing: universal-character-constant
@TOKEN(sub(r'({D}|\.{D})({D}|{L}|e[+-]|E[+-]|p[+-]|P[+-]|\.)*'))
def t_PP_pp_number(t):
    t.type = 'PP_NUMBER'
    return t
    
@TOKEN(CHARACTER_CONSTANT)
def t_PP_character_constant(t):
    t.type = 'CHARACTER_CONSTANT'
    return t

@TOKEN(STRING_LITERAL)
def t_PP_string_literal(t):
    t.type = 'STRING_LITERAL'

def t_PP_lparen(t):
    r'\('
    if t.lexer.lexdata[t.lexer.lexpos-2] not in (' \t\f\v'):
        t.type = 'PP_LPAREN'
    else:
        t.type = '('
    return t

def t_PP_newline(t):
    r'\n'
    t.lexer.pop_state()
    t.lexer.lineno += 1
    t.type = 'PP_NEWLINE'
    return t

def t_PP_error(t):
    t.lexer.skip(1)

t_PP_ignore = ' \t\v\f'

# --------------------------------------------------------------------------
# SKIPTEXT state
# --------------------------------------------------------------------------

skiptext_punctuators = punctuators.copy()

@TOKEN(punctuator_regex(skiptext_punctuators))
def t_SKIPTEXT_punctuator(t):
    return None

def t_SKIPTEXT_hash(t):
    r'\#'
    nl = t.lexer.lexdata.rfind('\n', 0, t.lexer.lexpos)
    if t.lexer.lexdata[nl:t.lexpos-1].strip() != '':
        # Does not follow newline, it's a punctuator
        return None
    else:
        t.lexer.push_state('PPBEGIN')

        # If CParser says its ok to give hash token to parser, do so;
        # otherwise this pp is in the middle of something complicated,
        # so we'll need to parse it ourselves.
        if t.lexer.accept_preprocessor:
            t.type = 'PP_HASH'
            return t
        else:
            # TODO
            pass

def t_SKIPTEXT_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)
    return None

def t_SKIPTEXT_error(t):
    t.lexer.skip(1)

t_SKIPTEXT_ignore = ' \t\v\f'

# --------------------------------------------------------------------------
# INITIAL state
# --------------------------------------------------------------------------

# Generate hash token in INITIAL state.  Must follow whitespace containing
# at least one newline.
def t_hash(t):
    r'\#'
    nl = t.lexer.lexdata.rfind('\n', 0, t.lexer.lexpos)
    if t.lexer.lexdata[nl:t.lexpos-1].strip() != '':
        # Does not follow newline, it's a punctuator
        t.type = '#'
        return t
    else:
        # Start pp state (after hash, before keyword).
        t.lexer.push_state('PPBEGIN')

        # If CParser says its ok to give hash token to parser, do so;
        # otherwise this pp is in the middle of something complicated,
        # so we'll need to parse it ourselves.
        if t.lexer.accept_preprocessor:
            t.type = 'PP_HASH'
            return t
        else:
            # TODO
            pass

@TOKEN(sub('{L}({L}|{D})*'))
def t_check_type(t):
    if t.value in t.lexer.defines:
        # Messy: insert replacement text before lexpos, then move back
        # lexpos to read it.  len(replacement text) is always less than
        # lexpos, since its #define must have preceeded it.  This is not
        # true if #include processing is done (it is not currently, so
        # no problem).
        repl = t.lexer.defines[t.value]
        pos = t.lexer.lexpos
        t.lexer.lexdata = t.lexer.lexdata[:pos-len(repl)] + \
            repl + t.lexer.lexdata[pos:]
        t.lexer.lexpos -= len(repl)
        return None

    elif t.value in keywords:
        t.type = t.value.upper()
    elif t.value in t.lexer.type_names:
        t.type = 'TYPE_NAME'
    else:
        t.type = 'IDENTIFIER'
    return t

@TOKEN(sub('0[xX]{H}+{IS}?'))
def t_hex_literal(t):
    t.type = 'CONSTANT'
    return t

@TOKEN(sub('0{D}+{IS}?'))
def t_oct_literal(t):
    t.type = 'CONSTANT'
    return t

@TOKEN(sub('{D}+{IS}?'))
def t_dec_literal(t):
    t.type = 'CONSTANT'
    return t

@TOKEN(CHARACTER_CONSTANT)
def t_character_constant(t):
    t.type = 'CHARACTER_CONSTANT'
    return t

@TOKEN(FLOAT_CONSTANT)
def t_float_constant(t):
    t.type = 'CONSTANT'
    return t

@TOKEN(STRING_LITERAL)
def t_string_literal(t):
    t.type = 'STRING_LITERAL'
    return t

@TOKEN(punctuator_regex(punctuators))
def t_punctuator(t):
    t.type = punctuators[t.value][1]
    return t

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

t_ignore = ' \t\v\f'

def t_error(t):
    t.lexer.skip(1)


# --------------------------------------------------------------------------
# C Object Model
# --------------------------------------------------------------------------

class EvaluationContext(object):
    '''Interface for evaluating expression nodes.

    The context can either be preprocessor or runtime; the only difference
    is the handling of identifiers and the 'defined' unary function.
    '''
    is_preprocessor = False

    def is_defined(self, identifier):
        return False

    def evaluate_identifier(name):
        raise NotImplementedError('abstract')

    def evaluate_function(function, arguments):
        raise NotImplementedError('abstract')

class ExpressionNode(object):
    def evaluate(self, context):
        return 0

    def __str__(self):
        return ''

class ConstantExpressionNode(ExpressionNode):
    def __init__(self, value):
        self.value = value

    def evaluate(self, context):
        return self.value

    def __str__(self):
        return str(self.value)

class IdentifierExpressionNode(ExpressionNode):
    def __init__(self, identifier):
        self.identifier = identifier

    def evaluate(self, context):
        return context.evaluate_identifier(self.identifier)

    def __str__(self):
        return str(self.identifier)

class UnaryExpressionNode(ExpressionNode):
    def __init__(self, op, op_str, child):
        self.op = op
        self.op_str = op_str
        self.child = child

    def evaluate(self, context):
        return self.op(self.child.evaluate(context))

    def __str__(self):
        return '(%s %s)' % (self.op_str, self.child)

class BinaryExpressionNode(ExpressionNode):
    def __init__(self, op, op_str, left, right):
        self.op = op
        self.op_str = op_str
        self.left = left
        self.right = right

    def evaluate(self, context):
        return self.op(self.left.evaluate(context), 
                       self.right.evaluate(context))

    def __str__(self):
        return '(%s %s %s)' % (self.left, self.op_str, self.right)

class LogicalAndExpressionNode(ExpressionNode):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def evaluate(self, context):
        return self.left.evaluate(context) and self.right.evaluate(context)

    def __str__(self):
        return '(%s && %s)' % (self.left, self.right)

class LogicalOrExpressionNode(ExpressionNode):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def evaluate(self, context):
        return self.left.evaluate(context) or self.right.evaluate(context)

    def __str__(self):
        return '(%s || %s)' % (self.left, self.right)

class ConditionalExpressionNode(ExpressionNode):
    def __init__(self, condition, left, right):
        self.condition = condition
        self.left = left
        self.right = right

    def evaluate(self, context):
        if self.condition.evaluate(context):
            return self.left.evaluate(context)
        else:
            return self.right.evaluate(context)

    def __str__(self):
        return '(%s ? %s : %s)' % (self.condition, self.left, self.right)

class FunctionExpressionNode(ExpressionNode):
    def __init__(self, function, arguments):
        self.function = function
        self.arguments = arguments

    def evaluate(self, context):
        if type(self.function) == IdentifierExpressionNode and \
           self.function.identifier == 'defined' and \
           context.is_preprocessor and \
           len(self.arguments) == 1 and \
           type(self.arguments[0] == IdentifierExpressionNode):
            return context.is_defined(self.arguments[0].identifier)
        else:
            args = [a.evaluate(context) for a in self.arguments]
            return context.evaluate_function(self.function.evaluate(context), 
                                             args)

    def __str__(self):
        return '%s(%s)' % \
            (self.function, ', '.join([str(a) for a in self.arguments]))

class Declaration(object):
    def __init__(self):
        self.declarator = None
        self.type = Type()
        self.storage = None

    def __repr__(self):
        d = {
            'declarator': self.declarator,
            'type': self.type,
        }
        if self.storage:
            d['storage'] = self.storage
        l = ['%s=%r' % (k, v) for k, v in d.items()]
        return 'Declaration(%s)' % ', '.join(l)

class Declarator(object):
    pointer = None
    def __init__(self):
        self.identifier = None
        self.initializer = None
        self.array = None
        self.parameters = None

    def __repr__(self):
        s = self.identifier or ''
        if self.array:
            s += repr(self.array)
        if self.initializer:
            s += ' = %r' % self.initializer
        if self.parameters is not None:
            s += '(' + ', '.join([repr(p) for p in self.parameters]) + ')'
        return s

abstract_declarator = Declarator()

class Pointer(Declarator):
    pointer = None
    def __init__(self):
        super(Pointer, self).__init__()
        self.qualifiers = []

    def __repr__(self):
        q = ''
        if self.qualifiers:
            q = '<%s>' % ' '.join(self.qualifiers)
        return 'POINTER%s(%r)' % (q, self.pointer) + \
            super(Pointer, self).__repr__()

class Array(object):
    def __init__(self):
        self.size = None
        self.array = None

    def __repr__(self):
        if self.size:
            a =  '[%r]' % self.size
        else:
            a = '[]'
        if self.array:
            return repr(self.array) + a
        else:
            return a

class Parameter(object):
    def __init__(self):
        self.type = Type()
        self.storage = None
        self.declarator = None

    def __repr__(self):
        d = {
            'type': self.type,
        }
        if self.declarator:
            d['declarator'] = self.declarator
        if self.storage:
            d['storage'] = self.storage
        l = ['%s=%r' % (k, v) for k, v in d.items()]
        return 'Parameter(%s)' % ', '.join(l)


class Type(object):
    def __init__(self):
        self.qualifiers = []
        self.specifiers = []

    def __repr__(self):
        return ' '.join(self.qualifiers + self.specifiers)

# These are used only internally.

class StorageClassSpecifier(str):
    pass

class TypeSpecifier(str):
    pass

class TypeQualifier(str):
    pass

def apply_specifiers(specifiers, declaration):
    '''Apply specifiers to the declaration (declaration may be
    a Parameter instead).'''
    for s in specifiers:
        if type(s) == StorageClassSpecifier:
            if declaration.storage:
                p.parser.cparser.handle_error(
                    'Declaration has more than one storage class', 
                    p.lineno(1))
                return
            declaration.storage = s
        elif type(s) == TypeSpecifier:
            declaration.type.specifiers.append(s)
        elif type(s) == TypeQualifier:
            declaration.type.qualifiers.append(s)


# --------------------------------------------------------------------------
# Grammar
# --------------------------------------------------------------------------

def p_translation_unit(p):
    '''translation_unit : external_declaration
                        | translation_unit external_declaration
    '''
    # Starting production.
    # Intentionally empty

def p_identifier(p):
    '''identifier : IDENTIFIER'''
    p[0] = IdentifierExpressionNode(p[1])

def p_constant(p):
    '''constant : CONSTANT
                | PP_NUMBER
    '''
    p[0] = ConstantExpressionNode(p[1])

def p_string_literal(p):
    '''string_literal : STRING_LITERAL'''
    p[0] = ConstantExpressionNode(p[1])

def p_primary_expression(p):
    '''primary_expression : identifier
                          | constant
                          | string_literal
                          | '(' expression ')'
                          | PP_LPAREN expression ')'
    '''
    if p[1] == '(':
        p[0] = p[2]
    else:
        p[0] = p[1]

def p_postfix_expression(p):
    '''postfix_expression : primary_expression
                  | postfix_expression '[' expression ']'
                  | postfix_expression '(' ')'
                  | postfix_expression PP_LPAREN ')'
                  | postfix_expression '(' argument_expression_list ')'
                  | postfix_expression PP_LPAREN argument_expression_list ')'
                  | postfix_expression '.' IDENTIFIER
                  | postfix_expression PTR_OP IDENTIFIER
                  | postfix_expression INC_OP
                  | postfix_expression DEC_OP
    '''
    # Not handled: most of them.
    if len(p) == 2:
        p[0] = p[1]
    elif p[2] == '(':
        if p[3] == ')':
            p[0] = FunctionExpressionNode(p[1], ())
        else:
            p[0] = FunctionExpressionNode(p[1], p[3])
    else:
        # TODO
        p[0] = p[1]

def p_argument_expression_list(p):
    '''argument_expression_list : assignment_expression
                        | argument_expression_list ',' assignment_expression
    '''
    if len(p) == 2:
        p[0] = (p[1],)
    else:
        p[0] = p[1] + (p[3],)

def p_unary_expression(p):
    '''unary_expression : postfix_expression
                        | INC_OP unary_expression
                        | DEC_OP unary_expression
                        | unary_operator cast_expression
                        | SIZEOF unary_expression
                        | SIZEOF '(' TYPE_NAME ')'
                        | SIZEOF PP_LPAREN TYPE_NAME ')'
    '''
    if len(p) == 2:
        p[0] = p[1]
    elif type(p[1]) == tuple:
        # unary_operator reduces to (op, op_str)
        p[0] = UnaryExpressionNode(p[1][0], p[1][1], p[2])
    else:
        # TODO
        p[0] = None

def p_unary_operator(p):
    '''unary_operator : '&'
                      | '*'
                      | '+'
                      | '-'
                      | '~'
                      | '!'
    '''
    # TODO: most of these operators
    # reduces to (op, op_str)
    p[0] = ({
        '&': None,
        '*': None,
        '+': operator.pos,
        '-': operator.neg,
        '~': operator.inv,
        '!': operator.not_}[p[1]], p[1])

def p_cast_expression(p):
    '''cast_expression : unary_expression
                       | '(' TYPE_NAME ')' cast_expression
                       | PP_LPAREN TYPE_NAME ')' cast_expression
    '''
    # TODO
    p[0] = p[len(p) - 1]

def p_multiplicative_expression(p):
    '''multiplicative_expression : cast_expression
                                 | multiplicative_expression '*' cast_expression
                                 | multiplicative_expression '/' cast_expression
                                 | multiplicative_expression '%' cast_expression
    '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = BinaryExpressionNode({
            '*': operator.mul,
            '/': operator.div,
            '%': operator.mod}[p[2]], p[2], p[1], p[3])

def p_additive_expression(p):
    '''additive_expression : multiplicative_expression
                           | additive_expression '+' multiplicative_expression
                           | additive_expression '-' multiplicative_expression
    '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = BinaryExpressionNode({
            '+': operator.add,
            '-': operator.sub}[p[2]], p[2], p[1], p[3])

def p_shift_expression(p):
    '''shift_expression : additive_expression
                        | shift_expression LEFT_OP additive_expression
                        | shift_expression RIGHT_OP additive_expression
    '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = BinaryExpressionNode({
            '<<': operator.lshift,
            '>>': operator.rshift}[p[2]], p[2], p[1], p[3])

def p_relational_expression(p):
    '''relational_expression : shift_expression 
                             | relational_expression '<' shift_expression
                             | relational_expression '>' shift_expression
                             | relational_expression LE_OP shift_expression
                             | relational_expression GE_OP shift_expression
    '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = BinaryExpressionNode({
            '>': operator.gt,
            '<': operator.lt,
            '<=': operator.le,
            '>=': operator.ge}[p[2]], p[2], p[1], p[3])

def p_equality_expression(p):
    '''equality_expression : relational_expression
                           | equality_expression EQ_OP relational_expression
                           | equality_expression NE_OP relational_expression
    '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = BinaryExpressionNode({
            '==': operator.eq,
            '!=': operator.ne}[p[2]], p[2], p[1], p[3])

def p_and_expression(p):
    '''and_expression : equality_expression
                      | and_expression '&' equality_expression
    '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = BinaryExpressionNode(operator.and_, '&', p[1], p[3])

def p_exclusive_or_expression(p):
    '''exclusive_or_expression : and_expression
                               | exclusive_or_expression '^' and_expression
    ''' 
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = BinaryExpressionNode(operator.xor, '^', p[1], p[3])

def p_inclusive_or_expression(p):
    '''inclusive_or_expression : exclusive_or_expression
                       | inclusive_or_expression '|' exclusive_or_expression
    '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = BinaryExpressionNode(operator.or_, '|', p[1], p[3])

def p_logical_and_expression(p):
    '''logical_and_expression : inclusive_or_expression
                      | logical_and_expression AND_OP inclusive_or_expression
    '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = LogicalAndExpressionNode(p[1], p[3])

def p_logical_or_expression(p):
    '''logical_or_expression : logical_and_expression
                      | logical_or_expression OR_OP logical_and_expression
    '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = LogicalOrExpressionNode(p[1], p[3])

def p_conditional_expression(p):
    '''conditional_expression : logical_or_expression
              | logical_or_expression '?' expression ':' conditional_expression
    '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ConditionalExpressionNode(p[1], p[3], p[5])

def p_assignment_expression(p):
    '''assignment_expression : conditional_expression
                 | unary_expression assignment_operator assignment_expression
    '''
    # TODO assignment
    if len(p) == 2:
        p[0] = p[1]

def p_assignment_operator(p):
    '''assignment_operator : '='
                           | MUL_ASSIGN
                           | DIV_ASSIGN
                           | MOD_ASSIGN
                           | ADD_ASSIGN
                           | SUB_ASSIGN
                           | LEFT_ASSIGN
                           | RIGHT_ASSIGN
                           | AND_ASSIGN
                           | XOR_ASSIGN
                           | OR_ASSIGN
    '''

def p_expression(p):
    '''expression : assignment_expression
                  | expression ',' assignment_expression
    '''
    # TODO sequence
    if len(p) == 2:
        p[0] = p[1]

def p_constant_expression(p):
    '''constant_expression : conditional_expression
    '''
    p[0] = p[1]


def p_declaration(p):
    '''declaration : declaration_specifiers
                   | declaration_specifiers init_declarator_list
    '''
    declaration = Declaration()
    apply_specifiers(p[1], declaration)

    if len(p) == 2:
        p.parser.cparser.impl_handle_declaration(declaration)
        return

    for declarator in p[2]:
        declaration.declarator = declarator
        p.parser.cparser.impl_handle_declaration(declaration)

    # ';' is being shifted now, so can accept PP again
    p.lexer.accept_preprocessor = True

def p_declaration_error(p):
    '''declaration : error ';'
    '''
    # Error resynchronisation catch-all

def p_declaration_specifiers(p):
    '''declaration_specifiers : storage_class_specifier
                              | storage_class_specifier declaration_specifiers
                              | type_specifier
                              | type_specifier declaration_specifiers
                              | type_qualifier
                              | type_qualifier declaration_specifiers
    '''
    if len(p) > 2:
        p[0] = (p[1],) + p[2]
    else:
        p[0] = (p[1],)

def p_init_declarator_list(p):
    '''init_declarator_list : init_declarator
                            | init_declarator_list ',' init_declarator
    '''
    if len(p) > 2:
        p[0] = p[1] + (p[3],)
    else:
        p[0] = (p[1],)

def p_init_declarator(p):
    '''init_declarator : declarator
                       | declarator '=' initializer
    '''
    p[0] = p[1]
    if len(p) > 2:
        p[0].initializer = p[2]

def p_storage_class_specifier(p):
    '''storage_class_specifier : TYPEDEF
                               | EXTERN
                               | STATIC
                               | AUTO
                               | REGISTER
    '''
    p[0] = StorageClassSpecifier(p[1])

def p_type_specifier(p):
    '''type_specifier : VOID
                      | CHAR
                      | SHORT
                      | INT
                      | LONG
                      | FLOAT
                      | DOUBLE
                      | SIGNED
                      | UNSIGNED
                      | struct_or_union_specifier
                      | enum_specifier
                      | TYPE_NAME
    '''
    # Not handled: struct_or_union_specifier, enum_specifier
    p[0] = TypeSpecifier(p[1])

def p_struct_or_union_specifier(p):
    '''struct_or_union_specifier : struct_or_union IDENTIFIER '{' struct_declaration_list '}'
         | struct_or_union '{' struct_declaration_list '}'
         | struct_or_union IDENTIFIER
    '''

def p_struct_or_union(p):
    '''struct_or_union : STRUCT
                       | UNION
    '''

def p_struct_declaration_list(p):
    '''struct_declaration_list : struct_declaration
                               | struct_declaration_list struct_declaration
    '''

def p_struct_declaration(p):
    '''struct_declaration : specifier_qualifier_list struct_declarator_list ';'
    '''

def p_specifier_qualifier_list(p):
    '''specifier_qualifier_list : type_specifier specifier_qualifier_list
                                | type_specifier
                                | type_qualifier specifier_qualifier_list
                                | type_qualifier
    '''

def p_struct_declarator_list(p):
    '''struct_declarator_list : struct_declarator
                              | struct_declarator_list ',' struct_declarator
    '''

def p_struct_declarator(p):
    '''struct_declarator : declarator
                         | ':' constant_expression
                         | declarator ':' constant_expression
    '''

def p_enum_specifier(p):
    '''enum_specifier : ENUM '{' enumerator_list '}'
                      | ENUM IDENTIFIER '{' enumerator_list '}'
                      | ENUM IDENTIFIER
    '''

def p_enumerator_list(p):
    '''enumerator_list : enumerator
                       | enumerator_list ',' enumerator
    '''

def p_enumerator(p):
    '''enumerator : IDENTIFIER
                  | IDENTIFIER '=' constant_expression
    '''

def p_type_qualifier(p):
    '''type_qualifier : CONST
                      | VOLATILE
    '''
    p[0] = TypeQualifier(p[1])

def p_declarator(p):
    '''declarator : pointer direct_declarator
                  | direct_declarator
    '''
    if len(p) > 2:
        p[0] = p[1]
        ptr = p[1]
        while ptr.pointer:
            ptr = ptr.pointer
        ptr.pointer = p[2]
    else:
        p[0] = p[1]

def p_direct_declarator(p):
    '''direct_declarator : IDENTIFIER
                         | '(' declarator ')'
                         | direct_declarator '[' constant_expression ']'
                         | direct_declarator '[' ']'
                         | direct_declarator '(' parameter_type_list ')'
                         | direct_declarator '(' identifier_list ')'
                         | direct_declarator '(' ')'
    '''
    if isinstance(p[1], Declarator):
        p[0] = p[1] 
        if p[2] == '[':
            a = Array()
            a.array = p[0].array
            p[0].array = a
            if p[3] != ']':
                a.size = p[3]
        else:
            if p[3] == ')':
                p[0].parameters = ()
            else:
                p[0].parameters = p[3]
    elif p[1] == '(':
        p[0] = p[2]
    else:
        p[0] = Declarator()
        p[0].identifier = p[1]

    # Check parameters for (void) and simplify to empty tuple.
    if p[0].parameters and len(p[0].parameters) == 1:
        param = p[0].parameters[0]
        if param.type.specifiers == ['void'] and not param.declarator:
            p[0].parameters = ()


def p_pointer(p):
    '''pointer : '*'
               | '*' type_qualifier_list
               | '*' pointer
               | '*' type_qualifier_list pointer
    '''
    if len(p) == 2:
        p[0] = Pointer()
    elif len(p) == 3:
        if type(p[2]) == Pointer:
            p[0] = Pointer()
            p[0].pointer = p[2]
        else:
            p[0] = Pointer()
            p[0].qualifiers = p[2]
    else:
        p[0] = Pointer()
        p[0].qualifiers = p[2]
        p[0].pointer = p[3]

def p_type_qualifier_list(p):
    '''type_qualifier_list : type_qualifier
                           | type_qualifier_list type_qualifier
    '''
    if len(p) > 2:
        p[0] = p[1] + (p[2],)
    else:
        p[0] = (p[1],)

def p_parameter_type_list(p):
    '''parameter_type_list : parameter_list
                           | parameter_list ',' ELLIPSIS
    '''
    if len(p) > 2:
        p[0] = p[1] + (p[3],)
    else:
        p[0] = p[1]


def p_parameter_list(p):
    '''parameter_list : parameter_declaration
                      | parameter_list ',' parameter_declaration
    '''
    if len(p) > 2:
        p[0] = p[1] + (p[3],)
    else:
        p[0] = (p[1],)

def p_parameter_declaration(p):
    '''parameter_declaration : declaration_specifiers declarator
                             | declaration_specifiers abstract_declarator
                             | declaration_specifiers
    '''
    p[0] = Parameter()
    apply_specifiers(p[1], p[0])
    if len(p) > 2:
        p[0].declarator = p[2]

def p_opt_identifier_list(p):
    '''opt_identifier_list : identifier_list
                           | 
    '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = []

def p_identifier_list(p):
    '''identifier_list : IDENTIFIER
                       | identifier_list ',' IDENTIFIER
    '''
    param = Parameter()
    param.declarator = Declarator()
    if len(p) > 2:
        param.declarator.identifier = p[3]
        p[0] = p[1] + (param,)
    else:
        param.declarator.identifier = p[1]
        p[0] = (param,)

def p_abstract_declarator(p):
    '''abstract_declarator : pointer
                           | direct_abstract_declarator
                           | pointer direct_abstract_declarator
    '''
    if len(p) == 2:
        p[0] = p[1]
        if type(p[0]) == Pointer:
            ptr = p[0]
            while ptr.pointer:
                ptr = ptr.pointer
            ptr.pointer = abstract_declarator
    else:
        p[0] = p[1]
        ptr = p[0]
        while ptr.pointer:
            ptr = ptr.pointer
        ptr.pointer = p[2]

def p_direct_abstract_declarator(p):
    '''direct_abstract_declarator : '(' abstract_declarator ')'
                      | '[' ']'
                      | '[' constant_expression ']'
                      | direct_abstract_declarator '[' ']'
                      | direct_abstract_declarator '[' constant_expression ']'
                      | '(' ')'
                      | '(' parameter_type_list ')'
                      | direct_abstract_declarator '(' ')'
                      | direct_abstract_declarator '(' parameter_type_list ')'
    '''
    if p[1] == '(' and isinstance(p[2], Declarator):
        p[0] = p[2]
    else:
        if isinstance(p[1], Declarator):
            p[0] = p[1]
            if p[2] == '[':
                a = Array()
                a.array = p[0].array
                p[0].array = a
                if p[3] != ']':
                    p[0].array.size = p[3]
            elif p[2] == '(':
                if p[3] == ')':
                    p[0].parameters = ()
                else:
                    p[0].parameters = p[3]
        else:
            p[0] = Declarator()
            if p[1] == '[':
                p[0].array = Array()
                if p[2] != ']':
                    p[0].array.size = p[2]
            elif p[1] == '(':
                if p[2] == ')':
                    p[0].parameters = ()
                else:
                    p[0].parameters = p[2]

def p_initializer(p):
    '''initializer : assignment_expression
                   | '{' initializer_list '}'
                   | '{' initializer_list ',' '}'
    '''

def p_initializer_list(p):
    '''initializer_list : initializer
                        | initializer_list ',' initializer
    '''

def p_external_declaration(p):
    '''external_declaration : declaration ';'
                            | pp_group_part
    '''
    # The ';' must be here, not in 'declaration', as declaration needs to
    # be executed before the ';' is shifted (otherwise the next lookahead will
    # be read, which may be affected by this declaration if its a typedef.

    # Not handled: function_definition
    # Special: pp_group_part 
    # Intentionally empty

def p_error(t):
    if not t:
        # Crap, no way to get to CParser instance.  FIXME TODO
        print >> sys.stderr, 'Syntax error at end of file.'
    else:
        t.lexer.cparser.handle_error('Syntax error at %r' % t.value, 
            t.lexer.lineno)
    # Don't alter lexer: default behaviour is to pass error production
    # up until it hits the catch-all at declaration, at which point
    # parsing continues (synchronisation).

# --------------------------------------------------------------------------
# Preprocessor grammar
# --------------------------------------------------------------------------

def p_pp_group_part(p):
    '''pp_group_part : pp_if_section PP_NEWLINE
                     | pp_control_line PP_NEWLINE
    '''
    # Not handled: text-line and non-directive (these are expanded by C grammar)
    # Special: NEW_LINE is here, so that directives are reduced before the
    #   newline is shifted, and the next lookahead won't be read until
    #   the grammar has had a chance to change the lexer's state.
    # Intentionally empty

def p_pp_if_section(p):
    '''pp_if_section : pp_if_group
                     | pp_elif_group
                     | pp_else_group
                     | pp_endif_line
    '''
    # Special: Can't handle elif-groups separately; will have to be resolved
    #   at some other level.
    # Intentionally empty

def p_pp_if_group(p):
    '''pp_if_group : PP_HASH PP_IF constant_expression 
                   | PP_HASH PP_IFDEF IDENTIFIER
                   | PP_HASH PP_IFNDEF IDENTIFIER
    '''

def p_pp_elif_group(p):
    '''pp_elif_group : PP_HASH PP_ELIF constant_expression
    '''

def p_pp_else_group(p):
    '''pp_else_group : PP_HASH PP_ELSE
    '''

def p_pp_endif(p):
    '''pp_endif_line : PP_HASH PP_ENDIF
    '''

def p_pp_control_line(p):
    '''pp_control_line : PP_HASH PP_INCLUDE pp_tokens
                       | PP_HASH PP_DEFINE pp_object pp_replacement_list
                       | PP_HASH PP_DEFINE pp_function pp_replacement_list
                       | PP_HASH PP_UNDEF IDENTIFIER
                       | PP_HASH PP_LINE pp_tokens
                       | PP_HASH PP_ERROR pp_opt_tokens
                       | PP_HASH PP_PRAGMA pp_opt_tokens
                       | PP_HASH
    '''
    # Special: pp_object and pp_function, for readability
    # There is a shift/reduce conflict on IDENTIFIER .  LPAREN (shift to
    #   pp_function or reduce to pp_token in pp_object replacement list).
    #   Default behaviour is to shift, which is correct in this situation.

def p_pp_object(p):
    '''pp_object : IDENTIFIER'''

def p_pp_function(p):
    '''pp_function : IDENTIFIER PP_LPAREN opt_identifier_list ')'
                   | IDENTIFIER PP_LPAREN ELLIPSIS ')'
                   | IDENTIFIER PP_LPAREN identifier_list ',' ELLIPSIS ')'
    '''

def p_pp_replacement_list(p):
    '''pp_replacement_list : pp_opt_tokens
    '''

def p_pp_opt_tokens(p):
    '''pp_opt_tokens : pp_tokens
                     |
    '''

def p_pp_tokens(p):
    '''pp_tokens : pp_preprocessing_token
                 | pp_tokens pp_preprocessing_token
    '''

def p_pp_preprocessing_token(p):
    '''pp_preprocessing_token : PP_HEADER_NAME
                              | IDENTIFIER
                              | PP_NUMBER
                              | CHARACTER_CONSTANT
                              | STRING_LITERAL
                              | punctuator
    '''

def p_punctuator(p):
    '''punctuator : ELLIPSIS 
                  | RIGHT_ASSIGN 
                  | LEFT_ASSIGN 
                  | ADD_ASSIGN
                  | SUB_ASSIGN 
                  | MUL_ASSIGN 
                  | DIV_ASSIGN 
                  | MOD_ASSIGN 
                  | AND_ASSIGN 
                  | XOR_ASSIGN 
                  | OR_ASSIGN 
                  | RIGHT_OP 
                  | LEFT_OP 
                  | INC_OP 
                  | DEC_OP 
                  | PTR_OP 
                  | AND_OP 
                  | OR_OP 
                  | LE_OP 
                  | GE_OP
                  | EQ_OP 
                  | NE_OP 
                  | HASH_HASH 
                  | ';' 
                  | '{' 
                  | '}' 
                  | ',' 
                  | ':' 
                  | '=' 
                  | '(' 
                  | ')' 
                  | '[' 
                  | ']' 
                  | PERIOD
                  | '&' 
                  | '!' 
                  | '~' 
                  | '-'
                  | '+' 
                  | '*' 
                  | '/' 
                  | '%' 
                  | '<' 
                  | '>' 
                  | '^' 
                  | '|' 
                  | '?' 
                  | '#'
                  | PP_LPAREN
    '''

# --------------------------------------------------------------------------
# Lexer
# --------------------------------------------------------------------------

class CLexer(lex.Lexer):
    def __init__(self):
        lex.Lexer.__init__(self)
        self.accept_preprocessor = True

    def token(self):
        result = lex.Lexer.token(self)
        self.accept_preprocessor = False
        return result

# --------------------------------------------------------------------------
# Parser
# --------------------------------------------------------------------------

class CParser(object):
    '''Parse a C source file.

    Subclass and override the handle_* methods.  Call `parse` with a string
    to parse.
    '''
    def __init__(self, stddef_types=True):
        self.lexer = lex.lex(cls=CLexer)
        self.lexer.defines = {}
        self.lexer.type_names = set()
        self.lexer.cparser = self

        self.parser = yacc.yacc(method='LALR') 
        self.parser.cparser = self

        if stddef_types:
            self.lexer.type_names.add('wchar_t')
            self.lexer.type_names.add('ptrdiff_t')
            self.lexer.type_names.add('size_t')
    
    def parse(self, data, debug=False):
        '''Parse a source string.

        If `debug` is True, parsing state is dumped to stdout.
        '''
        if not data.strip():
            return

        self.parser.parse(data, debug=debug)

    # ----------------------------------------------------------------------
    # Parser interface.  Override these methods in your subclass.
    # ----------------------------------------------------------------------

    def handle_error(self, message, lineno):
        '''A parse error occured.  
        
        The default implementation prints `lineno` and `message` to stderr.
        The parser will try to recover from errors by synchronising at the
        next semicolon.
        '''
        print >> sys.stderr, '%s:' % lineno, message

    def handle_define(self, name, value):
        '''#ifdef `name` `value` (both are strings)'''
        pass

    def handle_undef(self, name):
        '''#undef `name`'''
        pass

    def handle_if(self, expr):
        '''#if `expr`'''
        self.lexer.push_state(self.lexer.lexstate)

    def handle_ifdef(self, name):
        '''#ifdef `name`'''
        if name == '__cplusplus':
            self.lexer.push_state('ppskip')
        else:
            self.lexer.push_state(self.lexer.lexstate)

    def handle_ifndef(self, name):
        '''#ifndef `name`'''
        self.lexer.push_state(self.lexer.lexstate)

    def handle_endif(self):
        '''#endif'''
        self.lexer.pop_state()
        pass

    def impl_handle_declaration(self, declaration):
        '''Internal method that calls `handle_declaration`.  This method
        also adds any new type definitions to the lexer's list of valid type
        names, which affects the parsing of subsequent declarations.
        '''
        if declaration.storage == 'typedef':
            declarator = declaration.declarator
            if not declarator:
                # XXX TEMPORARY while struct etc not filled
                return
            while declarator.pointer:
                declarator = declarator.pointer
            self.lexer.type_names.add(declarator.identifier)
        self.handle_declaration(declaration)

    def handle_declaration(self, declaration):
        '''A declaration was encountered.  
        
        `declaration` is an instance of Declaration.  Where a declaration has
        multiple initialisers, each is returned as a separate declaration.
        '''
        pass

class DebugCParser(CParser):
    '''A convenience class that prints each invocation of a handle_* method to
    stdout.
    '''
    def handle_define(self, name, value):
        print '#define name=%r, value=%r' % (name, value)

    def handle_undef(self, name):
        print '#undef name=%r' % name

    def handle_if(self, expr):
        print '#if expr=%r' % expr
        super(DebugCParser, self).handle_if(expr)

    def handle_ifdef(self, name):
        print '#ifdef name=%r' % name
        super(DebugCParser, self).handle_ifdef(name)

    def handle_ifndef(self, name):
        print '#ifndef name=%r' % name
        super(DebugCParser, self).handle_ifndef(name)

    def handle_endif(self):
        print '#endif'
        super(DebugCParser, self).handle_endif()

    def handle_declaration(self, declaration):
        print declaration
        
if __name__ == '__main__':
    import sys
    file = sys.argv[1]
    DebugCParser().parse(open(file).read(), debug=1)
