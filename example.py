from lexer import Lexer
from parser import Parser

from threading import Thread
from timeit import Timer

import extern as rbt

import math

rbt.add_basic_types()
rbt.add_basic_funcs()

rbt.add_type(complex,
    [rbt.Arg("real", (int, float)), rbt.Arg("imaginary", (int, float))],
    {"real", "imag"},
    {"conjugate" : []}
)

rbt.add_builtins(
    rbt.BuiltinFunc("print", [rbt.Varg("args")], print),
    rbt.BuiltinFunc("input", [rbt.Arg("prompt", str)], input, type=str)
)

try:
    # A Lexer represents a single translation unit,
    # so one script, isolated from the rest
    with open("example.rbt", "r") as f:
        l = Lexer(f.read(), "test_program").tokenize()
    # print(l.tokens)

    p = Parser(l)
    AST = p.parse_AST()

    # Parallel execution
    t : Thread = AST.new_thread()
    t.start()

    # Time the execution
    print(f"time = {Timer(AST.execute).timeit(1):.5f} seconds")

    t.join(1.0)
except Exception as e:
    if type(e) == Exception:
        print(e)
    else:
        raise e
