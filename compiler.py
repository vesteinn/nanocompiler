import sys
from lexer import find_column
from lexer import NMLexer
from parser import NMParser, Stack
import pprint


class NMCompiler(object):

    def __init__(self, intermediate, name, dbg=False):
        self.inter = intermediate
        self.ass = []
        self.name = name
        self.debug = dbg
        self.next_lab = 1

    def new_lab(self):
        prev_lab = self.next_lab
        self.next_lab += 1
        return prev_lab
        
    def emit(self, v):
        self.ass.append(v)
        if self.debug:
            print v

    def compile(self):
        self.generate_program()
        fname = self.name + ".masm"
        o = open(fname, 'w')
        for line in self.ass:
            o.writelines(line + "\n")
        print '{} written.'.format(fname)

    def generate_program(self):
        self.emit('"{}.mexe" = main in'.format(self.name))
        self.emit("!{{")
        for func in self.inter:
            self.generate_function(func)
        self.emit('}}*BASIS;')

    def generate_function(self, func):
        _f, fname, argcount, vars, exprs = func
        self.emit('#"{}[f{}]" ='.format(fname, argcount))
        self.emit('[')

        if vars:
            for _v in range(argcount) + vars:
                self.emit('(MakeVal null)')
                self.emit('(Push)')

        self.generate_expr(exprs[0])
        for expr in exprs[1:]:
            self.generate_expr(expr)

        self.emit("(Return)")
        self.emit('];')

    def generate_expr(self, expr):
        if not expr:
            return
        elif expr[0] == 'Store':
            self.generate_expr(expr[2])
            self.emit('(Store {})'.format(expr[1]))
        elif expr[0] == 'Fetch':
            self.emit('(Fetch {})'.format(expr[1]))
        elif expr[0] == 'Literal':
            self.emit('(MakeVal {})'.format(expr[1]))
        elif expr[0] == 'if':
            # if cond then elsifs else
            lab_else = self.new_lab()
            lab_end = self.new_lab()
            self.generate_jump(expr[1], 0, lab_else)
            for e in expr[2]:
                self.emit("(Push)")
                self.generate_expr(e)
            self.emit("(Go _{})".format(lab_end))
            self.emit("_{}:".format(lab_else))
            if not expr[3]:
                # No elseifs, only else
                for e in expr[4]:
                    self.generate_expr(e)
            else:
                new_expr = expr[3][0]
                # Change to if for nesting
                new_expr[0] = 'if'
                # New elsif's, if any
                try:
                    new_expr.a(expr[3][1:])
                    new_expr.a(expr[4])
                except:
                    new_expr.append(expr[3][1:])
                    new_expr.append(expr[4])
                self.generate_expr(new_expr)
            self.emit("_{}:".format(lab_end))
        elif expr[0] == 'while':
            lab_start = self.new_lab()
            lab_end = self.new_lab()
            self.emit("_{}:".format(lab_start))
            self.generate_jump(expr[1], 0, lab_end)
            for e in expr[2]:
                self.generate_expr(e)
            self.emit("(Go _{})".format(lab_start))
            self.emit("_{}:".format(lab_end))
        elif expr[0] == 'Call':
            if expr[3]:
                self.generate_expr(expr[3][0])
            for e in expr[3][1:]:
                self.emit("(Push)")
                self.generate_expr(e)
            self.emit('(Call #"{0}[f{1}]" {1})'.format(expr[1], expr[2]))
        elif expr[0] == 'return':
            self.generate_expr(expr[1])
            self.emit("(Return)")

    def generate_jump(self, expr, labtrue, labfalse):
        self.generate_expr(expr)
        if labtrue != 0:
            self.emit("(GoTrue _{})".format(labtrue))
        if labfalse != 0:
            self.emit("(GoFalse _{})".format(labfalse))


if __name__ == '__main__':

    filename = sys.argv[1]
    debug = len(sys.argv) > 2 and sys.argv[2] == "debug"

    f = open(filename)
    data = f.read()
    f.close()

    print("Initiating lexer.")
    nmlexer = NMLexer(strict=True)
    nmlexer.build()

    nmlexer.lexer.input(data)

    token_data = []

    print("Lexing")
    while True:
        tok = nmlexer.lexer.token()
        if not tok:
            break
        col = find_column(data, tok)
        if len(sys.argv) == 3 and debug:
            sys.stdout.write('%s\t%r\t%d\t%d\n' % (tok.type, tok.value, tok.lineno, col))
        tok.col = col
        token_data.append(tok)

    print("Initiating parsing.")
    parser = NMParser(input=token_data)
    print("Starting parsing")
    parser.program()
    print("Parsing OK!")
    print("Printing intermediate assembly")
    if debug:
        pprint.pprint(parser.intermediate)

    compiler = NMCompiler(parser.intermediate, filename.split('/')[-1].split('.')[0], debug)
    print("Compiling")
    compiler.compile()
    if debug:
        print "Compiling"
        import os
        os.system('java -jar morpho.jar -c fibo.masm')