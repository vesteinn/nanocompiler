import ply.lex as lex
from ply.lex import TOKEN

import sys


class NMLexer(object):

    KEYWORDS = {
        'else': 'else',
        'elsif': 'elsif',
        'if': 'if',
        'var': 'var',
        'while': 'while',
        'return': 'return'
    }

    literals = (
        '(',
        ')',
        '{',
        '}',
        ',',
        ';',
        '='
    )

    tokens = [
        'LITERAL',
        'NAME',
        'OPNAME',
        'ID'  # For matching reserved words
    ]

    tokens += list(KEYWORDS.values())

    def __init__(self, strict=False):
        self.strict = strict
        self.lexer = None

    # Line number tracking
    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)

    t_ignore = ' \t'
    t_OPNAME = r'[\*\/\%\+\-\<\>\!\&\?\~\^]'

    def t_ID(self, t):
        r'[a-z]+'
        t.type = self.KEYWORDS.get(t.value, 'NAME')
        return t

    def t_NAME(self, t):
        r'[^\W\d][^\W]*'
        return t

    r_double = r'(-?[0-9]+\.[0-9]+)'
    r_integer = r'(-{0,1}[0-9]+)'
    char_subpatterns = (
        r"[^'\"]",
        r"\\'",
        r"\\",
        r"\\n",
        r"\\t",
        r"\\b",
        r"\\f",
        r"\\[0-3]{0,1}[0-7]{1,2}",
    )
    char_identifier = r"\'(" + r"|".join(subp for subp in char_subpatterns) + r")\'"
    string_identifier = r'\"(' + "|".join(
        "(" + subp + ")*" for subp in char_subpatterns
    ) + r')\"'
    literal_identifier = "|".join((r_double, r_integer, char_identifier, string_identifier))
    @TOKEN(literal_identifier)
    def t_LITERAL(self, t):
        return t

    def t_error(self, t):
        message = "Illegal character '%s'" % t.value[0]
        if self.strict:
            raise Exception(message)
        print message
        t.lexer.skip(1)

    def build(self, **kwargs):
        self.lexer = lex.lex(module=self, **kwargs)

    def write(self):
        while True:
            tok = self.lexer.token()
            if not tok:
                break
            col = find_column(data, tok)
            sys.stdout.write('%s\t%r\t%d\t%d\n' % (tok.type, tok.value, tok.lineno, col))


def find_column(input, token):
    last_cr = input.rfind('\n', 0, token.lexpos)

    if last_cr < 0:
        last_cr = 0
    column = (token.lexpos - last_cr)

    return max(1, column)


if __name__ == '__main__':

    filename = sys.argv[1]
    f = open(filename)
    data = f.read()
    f.close()

    nmlexer = NMLexer()
    nmlexer.build()

    nmlexer.lexer.input(data)

    nmlexer.write()
