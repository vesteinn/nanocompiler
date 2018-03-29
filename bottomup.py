import ply.yacc as yacc
from lexer import NMLexer
from compiler import NMCompiler
import sys
import pprint
import os


tokens = NMLexer.tokens
KEYWORDS = NMLexer.KEYWORDS
literals = NMLexer.literals


precedence = (
    ('right', 'return'),
    ('left', 'OPNAME'),
)


from collections import defaultdict
names = defaultdict(list)


class Names(list):
    def pop(self):
        return self[-1]

    def push(self):
        return self.append([])


names = Names()


def p_program(p):
    """
    program : function program
           | function
    """
    if len(p) > 2:
        p[0] = [p[1]] + p[2]
    else:
        p[0] = [p[1]]


def p_empty(t):
    """empty :"""
    pass


def p_function(p):
    """
    function : new_scope NAME '(' named_args ')' '{' decl body '}'
    """

    p[0] = ['Func', p[2], len(p[4]), p[7], p[8]]
    names.pop()


def p_new_scope(p):
    """
    new_scope :
    """
    names.push()


def p_named_args(p):
    """
    named_args : NAME ',' named_args
        | NAME
        | empty
    """

    if len(p) > 2:
        for arg in p[3]:
            namesp[-1].append(arg)
        p[0] = [p[1]] + p[3]
    elif p[1] is not None:
        p[0] = [p[1]]
        names[-1].append(p[1])
    else:
        p[0] = []


def p_expression_name(p):
    """
    expr : NAME
    """
    p[0] = ['Fetch', names[-1].index(p[1])]


def p_body(p):
    """
    body : expr ';' body
         | expr ';'
    """
    if len(p) > 3:
        p[0] = [p[1]] + p[3]
    else:
        p[0] = [p[1]]


def p_statement_assign(p):
    """
    expr : NAME '=' expr
    """
    p[0] = ['Store', names[-1].index(p[1]), p[3]]


def p_args(p):
    """
    args : NAME ',' args
        | NAME
    """
    if len(p) > 2:
        p[0] = [p[1]] + p[3]
    else:
        p[0] = [p[1]]


def p_decl(p):
    """
    decl : var args ';' decl
         | empty
    """
    if len(p) > 2:
        for arg in p[2]:
            names[-1].append(arg)
        p[0] = ['Push'] * len(p[2])
    else:
        p[0] = ['Push']


def p_expression_args(p):
    """
    expr : NAME '(' expr_comma ')'
    """
    p[0] = ['Call', p[1], len(p[3]),  p[3]]



def p_expr_comma(p):
    """
    expr_comma : expr ',' expr_comma
               | expr
               | empty
    """
    if len(p) > 2:
        p[0] = [p[1]] + p[3]
    else:
        p[0] = [p[1]]


def p_expr_return(p):
    """
    expr : return expr
    """
    p[0] = ['return', p[2]]


def p_binary_operators(p):
    """
    expr : expr OPNAME expr
    """
    p[0] = ['Call', p[2], 2, [p[1], p[3]]]



def p_expression_number(p):
    """
    expr : LITERAL
    """
    p[0] = ['Literal', p[1]]


def p_ifexpr(p):
    """
    expr : if '(' expr ')' '{' body '}' elsifs elses
    """
    p[0] = ['if', p[3], p[6], p[8], p[9]]


def p_elsifs(p):
    """
    elsifs : elsif '(' expr ')' '{' body '}' elsifs
           | empty
    """
    if len(p) > 6:
        p[0] = [['elsif', p[3], p[6]]] + p[8]
    elif len(p) > 4:
        p[0] = [['elsif', p[3], p[6]]]
    else:
        p[0] = []


def p_elses(p):
    """ elses : else '{' body '}'
             | empty """
    if len(p) > 3:
        p[0] = p[3]
    else:
        p[0] = []


def p_while(p):
    """ expr : while '(' expr ')' '{' body '}' """
    p[0] = ['while', p[3], p[6]]


def p_expression_group(p):
    """
    expr :  '(' expr ')'
    """
    p[0] = p[2]


def p_error(t):
    print("Syntax error at {} in {}".format(t.value, t.lineno))


if __name__ == '__main__':

    filename = sys.argv[1]
    debug = len(sys.argv) > 2 and sys.argv[2] == "debug"

    f = open(filename)
    data = f.read()
    f.close()

    print("Initiating lexer.")
    nmlexer = NMLexer(strict=True)
    nmlexer.build()

    parser = yacc.yacc()

    parsed = parser.parse(data, debug=False)

    print names

    print "\n ----- COMPILING ---- \n"

    pprint.pprint(parsed)

    compiler = NMCompiler(parsed, filename.split('/')[-1].split('.')[0], debug)

    compiler.compile()

    os.system('java -jar morpho.jar -c fibo.masm')