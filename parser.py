class Stack(list):
    def a(self, *args, **kwargs):
        return self.append(*args, **kwargs)


class NMParser(object):
    """
    Parser for NanoMorpho.
    """

    ERROR_STRING = "{} is not the same as {} in {}, {}"
    EXPR_FIRST = (
        'NAME',
        'return',
        'OPNAME',
        'LITERAL',
        '{',
        'if',
        'while',
        '('
    )

    # Intermediate representation
    intermediate = []
    temp_vars = []

    def __init__(self, input):
        self.input = input

    def over(self, expected_type):
        if self.input:
            next_token = self.input.pop(0)
            if next_token.type == expected_type:
                data = (next_token.type, next_token.value)
                return data

        error = self.ERROR_STRING.format(
            next_token.type,
            expected_type,
            next_token.lineno,
            next_token.col
        )
        raise Exception(error)

    def check(self, expected_type, raise_error=False):
        if self.input:
            next_token = self.input[0]
            if hasattr(expected_type, '__iter__'):
                if next_token.type in expected_type:
                    return next_token
            elif next_token.type == expected_type:
                return next_token
            if raise_error:
                error = self.ERROR_STRING.format(
                    next_token.type,
                    expected_type,
                    next_token.lineno,
                    next_token.col
                )
                raise Exception(error)
        return None

    def program(self):
        while self.input:
            self.intermediate.append(self.function())

    def function(self):
        s = Stack()

        # All vars are local
        self.temp_vars = []

        s.a('Func')
        # Push name of function
        s.a((self.over('NAME'))[1])
        self.over('(')

        while self.check('NAME'):
            self.temp_vars.append(self.over('NAME')[1])
            while self.check(','):
                self.over(',')

        # Set args count
        s.a(len(self.temp_vars))

        self.over(')')
        self.over('{')

        if not self.check('var'):
            s.a([])

        while self.check('var'):
            s.a(self.decl())
            self.over(';')

        exprs = Stack()
        exprs.a(self.expr())
        self.over(';')
        while self.check(self.EXPR_FIRST):
            exprs.a(self.expr())
            self.over(';')
        s.a(exprs)

        self.over('}')
        self.temp_vars = []
        return s

    def decl(self):
        s = Stack()
        self.over('var')

        s.a('Push')
        var = self.over('NAME')
        self.temp_vars.append(var[1])

        while self.check(','):
            self.over(',')
            s.a('Push')
            var = self.over('NAME')
            self.temp_vars.append(var[1])

        return s

    def expr_inner(self):
        s = Stack()
        if self.check('NAME'):
            name = self.over('NAME')
            if self.check('='):
                # Assigning variable
                s.a('Store')
                # Get index in variable stack
                s.a(self.temp_vars.index(name[1]))
                self.over('=')
                s.a(self.expr())
            elif self.check('('):
                # Calling something
                s.a('Call')
                s.a(name[1])
                self.over('(')
                inner = Stack()
                while self.check(self.EXPR_FIRST):
                    inner.a(self.expr())
                    if self.check(','):
                        self.over(',')
                    else:
                        break
                s.a(len(inner))
                s.a(inner)
                self.over(')')
            else:
                s = self.expr(['Fetch', self.temp_vars.index(name[1])])
        elif self.check('return'):
            s.a(self.over('return')[1])
            s.a(self.expr())
        elif self.check('OPNAME'):
            s.a(self.expr(['Call', self.over('OPNAME')[1]]))
        elif self.check('LITERAL'):
            s.a('Literal')
            s.a(self.over('LITERAL')[1])
        elif self.check('('):
            self.over('(')
            s.a(self.expr())
            self.over(')')
        elif self.check('if'):
            s = self.ifexpr()
        elif self.check('while'):
            s.a(self.over('while')[1])
            self.over('(')
            s.a(self.expr())
            self.over(')')
            s.a(self.body())
        return s

    def expr(self, inner=None):
        s = Stack()
        if inner is None:
            inner = self.expr_inner()
        opexpr = self.check('OPNAME')
        if opexpr:
            s.a('Call')
            s.a(self.over('OPNAME')[1])
            s.a(2)
            if len(inner) == 1:
                inner = inner[0]
            s.a(Stack((inner, self.expr())))
        else:
            s = inner
        return s

    def ifexpr(self):
        s = Stack()
        s.a(self.over('if')[1])
        self.over('(')
        s.a(self.expr())
        self.over(')')
        s.a(self.body())

        elsifs = Stack()
        while self.check('elsif'):
            elsifs.a(self.elsif())
        s.a(elsifs)

        if self.check('else'):
            self.over('else')
            s.a(self.body())
        else:
            s.a(Stack())

        return s

    def elsif(self):
        s = Stack()
        s.a(self.over('elsif')[1])
        self.over('(')
        s.a(self.expr())
        self.over(')')
        s.a(self.body())
        return s

    def body(self):
        s = Stack()
        self.over('{')
        s.a(self.expr())
        self.over(';')
        while self.check(self.EXPR_FIRST):
            s.a(self.expr())
            self.over(';')
        self.over('}')
        return s

