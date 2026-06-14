from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Callable, override
from types import NoneType
from enum import Enum

from lexer import *
from AST import *

class Parser:
    def __init__(self, lexer : Lexer):
        self.__lexer : Lexer = lexer
        self.__tk_index : int = -1

    @property
    def lexer(self) -> Lexer:
        return self.__lexer

    @property
    def current(self) -> Token:
        return self.peek(0)

    def peek(self, ahead : int = 1, type : TkType | tuple[TkType] | None = None, content : str | tuple[str] | None = None) -> Token | None:
        """Check the nth token ahead and return it if it has the right type and / or content"""
        if not (0 <= self.__tk_index + ahead < len(self.lexer.tokens)):
            return None
        tk : Token = self.lexer.tokens[self.__tk_index + ahead]
        if (isinstance(type, tuple) and not (tk.type in type)) or \
           (isinstance(type, TkType) and tk.type != type):
            return None
        if (isinstance(content, tuple) and not (tk.content in content)) or \
           (isinstance(content, str) and tk.content != content):
            return None
        return tk

    def consume(self, ahead : int = 1, type : TkType | tuple[TkType] | None = None, content : str | tuple[str] | None = None) -> Token | None:
        """Consume the n tokens ahead if nth token ahead has the right type and / or content"""
        tk : Token | None = self.peek(ahead, type, content)
        if tk: self.__tk_index += ahead
        return tk

    def ensure(self, name : str, type : TkType | tuple[TkType] | None = None, content : str | tuple[str] | None = None) -> Token:
        """Ensure next token has of the right type and / or content"""
        tk : Token | None = self.consume(1, type, content)
        if tk is None:
            self.lexer.exception(f"Missing {name} after '{self.current.content}'", self.current)
        return tk

    # Pratt Parser
    def bp(self, operator : str) -> int:
        """Binding power of an operator"""
        BP : dict[str, int] = {
            "and": 1,
            "xor": 1,
            "or" : 1,
            "$not":2,
            "==": 3,
            "~=": 3,
            "!=": 3,
            ">" : 3,
            "<" : 3,
            ">=": 3,
            "<=": 3,
            "|" : 4,
            "&" : 5,
            "+" : 6,
            "-" : 6,
            "*" : 7,
            "/" : 7,
            "%" : 7,
            "$neg": 7,
            "^" : 8,
            "." : 100,
            "[" : 100,
            "(" : 100
        }
        return BP.get(operator, -1)

    def nud(self) -> Expr:
        if self.peek(type=(TkType.NAME, TkType.NUMBER, TkType.STRING, TkType.TRUE, TkType.FALSE, TkType.NOTHING)):
            return Term(self.consume())
        elif self.peek(content="-"):
            return Operation(self.consume(), self.expr(self.bp("$neg")))
        elif self.peek(content="not"):
            return Operation(self.consume(), self.expr(self.bp("$not")))
        elif self.peek(content="*"):
            return Unwrap(self.consume(), self.expr(self.bp("^")))
        elif self.consume(content="("):
            return self.expr()
        elif self.consume(content="["):
            op : Token = self.peek(-1)
            elems : list[Expr] = self.parse_args("]")
            self.ensure("closing ']'", content="]")
            return ListLiteral(op, elems)
        elif self.consume(content="{"):
            op : Token = self.peek(-1)
            elems : list[tuple[Expr, Expr]] = []
            while self.peek() and self.peek(content="}") is None:
                key : Expr = self.expr()
                self.ensure("delimiter ':'", content=":")
                value : Expr = self.expr()
                elems.append((key, value))
                if self.consume(content=",") is None: break
            self.ensure("closing '}'", content="}")
            return DictLiteral(op, elems)
        else:
            self.lexer.exception(f"Missing expression after '{self.current.content}'", self.current)

    def led(self, left : Expr, operator : Token) -> Expr:
        if operator == "^":
            return Operation(operator, left, self.expr(self.bp(operator.content) - 1))
        elif operator == ".":
            return Access(left, self.ensure("property name", type=TkType.NAME))
        elif operator == "[":
            expr : Expr = Operation(operator, left, self.expr())
            self.ensure("closing ']'", content="]")
            return expr
        elif operator == "(":
            expr : Expr = FuncCall(left, self.parse_args())
            self.ensure("closing ')'", content=")")
            return expr
        return Operation(operator, left, self.expr(self.bp(operator.content)))

    def expr(self, rbp : int = 0) -> Expr:
        left : Expr = self.nud()
        while(self.peek() and self.bp(self.peek().content) > rbp):
            left = self.led(left, self.consume())
        return left

    def parse_args(self, end : str = ")") -> list[Expr]:
        args : list[Expr] = []
        while self.peek() and self.peek(content=end) is None:
            args.append(self.expr())
            if self.consume(content=",") is None:
                break
        return args

    def parse_type(self) -> type | tuple[type]:
        types : list[type] = []
        while True:
            type : str = self.ensure("type name", type=(TkType.NAME, TkType.NOTHING)).content
            if not (type in Context.types):
                self.lexer.exception(f"Unknown type '{type}'", self.current)
            types.append(Context.types[type])
            if self.consume(content="|") is None:
                break
        if len(types) == 1:
            return types[0]
        return tuple(types)

    def parse_bracket_scope(self, parent : Statement):
        last : Statement | None = None
        while self.peek() and self.peek(content="}") is None:
            last = self.parse_stmt(parent, last)
            parent.add_stmt(last)

    def parse_indentation_scope(self, parent : Statement, parent_indent : int):
        last : Statement | None = None
        indent : int = self.peek().offset
        if indent <= parent_indent:
            self.lexer.exception("Expected indented block after ':'", self.current)
        while self.peek():
            if self.peek().offset != indent and self.peek().offset != parent_indent:
                self.lexer.exception("Inconsistent indentation", self.peek())
            if self.peek().offset == parent_indent:
                break
            last = self.parse_stmt(parent, last)
            parent.add_stmt(last)

    def parse_scope(self, parent : Statement, parent_indent : int):
        if self.consume(content=":"):
            self.parse_indentation_scope(parent, parent_indent)
        else:
            self.ensure("opening '{'", content="{")
            self.parse_scope(func)
            self.ensure("closing '}'", content="}")

    def parse_stmt(self, parent : Statement, last : Statement | None) -> Statement:
        """Parse a singular statement"""

        # Variable creation
        if self.consume(content="var"):
            name : Token = self.ensure("variable name", type=TkType.NAME)
            val : Expr | None = None
            type : type | tuple[type] | None = None
            if self.consume(content=":"):
                type = self.parse_type()
            if self.consume(content="="):
                val = self.expr()
            return VarCreation(name, type=type, value=val, parent=parent)

        # Function definition
        if self.consume(content=("def", "fn", "func")):
            indent : int = self.current.offset
            name : Token = self.ensure("function name", type=TkType.NAME)

            # Parse arguments
            self.ensure("opening '('", content="(")

            args : list[Arg | Varg] = []
            while self.peek() and self.peek(content=")") is None:
                if self.peek(content=".") and self.peek(2,content=".") and self.consume(3,content="."):
                    # Variable argument (...name : type)
                    varg_name : Token = self.ensure("variable argument list name", type=TkType.NAME)
                    varg_type : type | tuple[type] | None = None
                    if self.consume(content=":"):
                         varg_type = self.parse_type()
                    args.append(Varg(varg_name.content, varg_type, varg_name))
                    break
                else:
                    # Normal argument (name : type = value)
                    arg_name : Token = self.ensure("argument name", type=TkType.NAME)
                    arg_type : type | tuple[type] | None = None
                    arg_value : Any = None
                    if self.consume(content=":"):
                        arg_type = self.parse_type()
                    if self.consume(content="="):
                        arg_value = self.expr().value(parent.context, self.lexer)
                    args.append(Arg(arg_name.content, arg_type, arg_value, arg_name))
                if self.consume(content=",") is None: break

            self.ensure("closing ')'", content=")")

            # Parse function type
            type : type | tuple[type] | None = None
            if self.peek(content="-") and self.consume(2,content=">"):
                type = self.parse_type()

            func = FuncDef(name, args, type, parent=parent)
            self.parse_scope(func, indent)

            return func

        # Return statement
        if self.consume(content="return"):
            return Return(self.expr(), parent=parent)

        # If statement
        if self.consume(content="if"):
            indent : int = self.current.offset
            if_stmt = If(self.expr(), parent=parent)
            self.parse_scope(if_stmt, indent)
            return if_stmt

        # Elif statement
        if self.consume(content="elif") or (self.peek(content="else") and self.consume(2, content="if")):
            indent : int = self.current.offset if self.current.content == "elif" else self.peek(-2).offset
            if not isinstance(last, (If, Elif)):
                self.lexer.exception("Must be preceded by an if or elif statement", self.current)
            elif_stmt = Elif(self.expr(), last, parent=parent)
            self.parse_scope(elif_stmt, indent)
            return elif_stmt

        # Else statement
        if self.consume(content="else"):
            indent : int = self.current.offset
            if not isinstance(last, (If, Elif)):
                self.lexer.exception("Must be preceded by an if or elif statement", self.current)
            else_stmt = Else(last, parent=parent)
            self.parse_scope(else_stmt, indent)
            return else_stmt

        # While statement
        if self.consume(content="while"):
            indent : int = self.current.offset
            while_stmt = While(self.expr(), parent=parent)
            self.parse_scope(while_stmt, indent)
            return while_stmt

        # For statement
        if self.consume(content="for"):
            indent : int = self.current.offset
            elems : list[Token] = [self.ensure("element name", type=TkType.NAME)]
            if self.consume(content=","):
                elems.append(self.ensure("second element name", type=TkType.NAME))
            if self.consume(content=","):
                self.lexer.exception("Maximum of 2 elements in iterator for loop", self.current)
            if self.consume(content="in"):
                for_stmt = ForIter(elems, self.expr(), parent=parent)
            else:
                if len(elems) > 1: self.lexer.exception("Cannot have more than 1 element in a step for loop", self.current)
                if not self.consume(content="from") and not self.consume(content="="):
                    self.lexer.exception(f"Expected either 'from' or '=' after '{elems[0].content}'", self.current)
                start : Expr = self.expr()
                self.ensure("'to' keyword", content="to")
                end : Expr = self.expr()
                step : Expr = Term(Token("1", TkType.NUMBER, 0))
                if self.consume(content=",") or self.consume(content="step"):
                    step = self.expr()
                for_stmt = ForStep(elems[0], start, end, step, parent=parent)
            self.parse_scope(for_stmt, indent)
            return for_stmt

        # Break statement
        if self.consume(content="break"):
            return Break(self.current, parent=parent)

        # Continue statement
        if self.consume(content="continue"):
            return Continue(self.current, parent=parent)

        # Expression statement
        expr : Expr = self.expr()

        # Variable assignment
        if self.consume(content="="):
            return VarAssignment(expr, self.expr(), parent=parent)
        return ExprStatement(expr, parent=parent)

        self.lexer.exception("Unknown statement", self.peek())

    def parse_AST(self) -> GlobalScope:
        """Parse the entirety of the program's AST"""
        self.__tk_index = -1
        gs = GlobalScope(self.lexer)
        last : Statement | None = None
        while self.peek():
            last = self.parse_stmt(gs, last)
            gs.add_stmt(last)
        return gs
