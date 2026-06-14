from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Callable, Iterable, KeysView, ItemsView, override
from types import NoneType
from enum import Enum

import math
from lexer import *

"""
Abstract Syntax Tree (AST) structure is represented here.

Expression -> computable value (numbers, calculations, function calls, etc.)
Statement -> computable instruction (assign variable, call procedurces, if, for, while, etc.)
Context -> variables, functions and types necessary for computations
"""

def type_to_str(type : type | tuple[type] | None) -> str:
    if type is None:
        return "any"
    if isinstance(type, tuple):
        return f"{"|".join([x.__name__ for x in type])}"
    return f"{type.__name__}"


class Nothing:
    """Nothing (alternative to None):
        nothing"""
    __instance : Nothing = None
    def __new__(cls) -> Nothing:
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __bool__(self) -> bool: return False
    def __str__(self) -> str: return "nothing"
    def __repr__(self) -> str: return str(self)

class Var:
    """Variables:
        var name : type = value"""
    def __init__(self, name : str, value : Any = Nothing(), type : type | tuple[type] | None = None, definition : Token | None = None):
        if not isinstance(name, str):
            raise TypeError("name must be a str")
        self.__name : str = name
        self.__type : type | None = type
        if value: self.value = value
        else: self.__value = None
        self.__definition : Token | None = definition

    @property
    def name(self) -> str:
        return self.__name

    @property
    def type(self) -> type | tuple[type] | None:
        return self.__type

    @property
    def value(self) -> Any:
        return self.__value

    @property
    def definition(self) -> Token | None:
        return self.__definition

    @value.setter
    def value(self, value : Any):
        if not self.compatible(value):
            raise Exception(f"Cannot assign {repr(value)} to {self.name}\n{repr(value)} is not of required type {type_to_str(self.type)}")
        self.__value : Any = value

    def compatible(self, val : Any) -> bool:
        if self.type is None or val == Nothing() or isinstance(val, self.type):
            return True
        return False

    def __str__(self) -> str:
        text : str = f"{self.name}"
        if self.type: text += f" : {type_to_str(self.type)}"
        return text

    def __repr__(self) -> str: return str(self)

class Arg(Var):
    """Arguments:
        name : type = default value"""
    def __init__(self, name : str, type : type | tuple[type] | None = None, value : Any = None, definition : Token | None = None):
        super().__init__(name, value, type, definition)

class Varg(Var):
    """Variable arguments:
        ...name : type"""
    def __init__(self, name : str, type : type | tuple[type] | None = None, definition : Token | None = None):
        super().__init__(name, None, type, definition)

    @override
    def __str__(self) -> str:
        text : str = f"...{self.name}"
        if self.type: text += f" : {type_to_str(self.type)}"
        return text

class Func(ABC):
    """Functions:
        function name(args) : type { ... }"""
    def __init__(self, name : str, args : list[Arg | Varg], type : type | tuple[type] | None = None, definition : Token | None = None):
        self.__name : str = name
        self.__args : list[Arg | Varg] = args
        self.__type : type | tuple[type] | None = type
        self.__definition : Token | None = definition

    @property
    def name(self) -> str:
        return self.__name

    @property
    def args(self) -> list[Arg | Varg]:
        return self.__args

    @property
    def type(self) -> type | tuple[type] | None:
        return self.__type

    @property
    def definition(self) -> Token | None:
        return self.__definition

    @abstractmethod
    def call(self, args : list[Any], where : Token, lexer : Lexer) -> Any:
        pass

    def get_args(self, args : list[Any], where : Token, lexer : Lexer) -> list[Any]:
        args = args.copy()
        ret : list[Any] = []
        for arg in self.args:
            if len(args) == 0 and not isinstance(arg, Varg) and arg.value is None:
                lexer.exception(f"Missing value for argument {arg}", where)
            while len(args) > 0 or arg.value:
                val : Any = args.pop(0) if len(args) > 0 else arg.value
                if not arg.compatible(val):
                    lexer.exception(f"{repr(val)} is incompatible for argument {arg}", where)
                ret.append(val)
                if not isinstance(arg, Varg): break
        if len(args) > 0:
            lexer.exception(f"Extra arguments {', '.join([repr(x) for x in args])} were not expected", where)
        return ret

    def ret_compatible(self, val : Any) -> bool:
        if self.type is None or val == Nothing() or isinstance(val, self.type):
            return True
        return False

class BuiltinFunc(Func):
    """Built-in functions (like math functions, print, input, etc.)"""
    def __init__(self, name : str, args : list[Arg | Varg], func : Callable, type : type | tuple[type] | None = None):
        super().__init__(name, args, type)
        self.__func : Callable = func

    @override
    def call(self, args : list[Any], where : Token, lexer : Lexer) -> Any:
        args = self.get_args(args, where, lexer)
        try:
            ret : Any = self.__func(*[None if x == Nothing() else x for x in args])
        except Exception as e:
            lexer.exception(f"{type(e).__name__} - {e}", where)
        if ret == None:
            return Nothing()
        if isinstance(ret, (KeysView, ItemsView)):
            return dict(ret)
        if not isinstance(ret, str) and isinstance(ret, Iterable):
            return [Nothing() if x is None else x for x in ret]
        return ret

class Expr(ABC):
    """Abstract concept of computable value"""
    @abstractmethod
    def value(self, context : Context, lexer : Lexer) -> Any:
        pass

    @property
    @abstractmethod
    def tk(self) -> Token:
        pass

    @abstractmethod
    def __str__(self) -> str:
        pass

    def __repr__(self) -> str: return str(self)

class Term(Expr):
    """Atomic expression (a single value)"""
    def __init__(self, val : Token):
        self.__val : Token = val

    @property
    def val(self) -> Token:
        return self.__val

    @override
    @property
    def tk(self) -> Token:
        return self.val

    @override
    def value(self, context : Context, lexer : Lexer) -> Any:
        if self.__val == TkType.NUMBER:
            try:
                x = int(self.__val.content, base=0)
            except:
                try:
                    x = float(self.__val.content)
                except:
                    lexer.exception("Invalid number", self.__val)
            return x
        elif self.__val == TkType.STRING:
            return self.__val.content[1:-1]
        elif self.__val == TkType.TRUE:
            return True
        elif self.__val == TkType.FALSE:
            return False
        elif self.__val == TkType.NOTHING:
            return Nothing()
        elif self.__val == TkType.NAME:
            if not (self.__val.content in context.vars):
                lexer.exception("Unknown variable", self.__val)
            v : Var = context.vars[self.__val.content]
            return v.value
        lexer.exception("Invalid term expression", self.__val)

    def __str__(self) -> str:
        return self.val.content

class ListLiteral(Expr):
    """List literal ([elem1, elem2, elem3, ...])"""
    def __init__(self, operator : Token, elems : list[Expr]):
        self.__operator : Token = operator
        self.__elems : list[Expr] = elems

    @override
    @property
    def tk(self) -> Token:
        return self.__operator

    @override
    def value(self, context : Context, lexer : Lexer) -> Any:
        val : list[Any] = []
        for x in self.__elems:
            if isinstance(x, Unwrap):
                val.extend(x.value(context, lexer))
            else:
                val.append(x.value(context, lexer))
        return val

    @override
    def __str__(self) -> str:
        return self.__elems

class DictLiteral(Expr):
    """Dictionary literal ({key1:val1, key2:val2, ...})"""
    def __init__(self, operator : Token, pairs : list[tuple[Expr, Expr]]):
        self.__operator : Token = operator
        self.__pairs : list[tuple[Expr, Expr]] = pairs

    @override
    @property
    def tk(self) -> Token:
        return self.__operator

    @override
    def value(self, context : Context, lexer : Lexer) -> Any:
        val : dict[Any, Any] = {}
        for k, v in self.__pairs:
            val[k.value(context, lexer)] = v.value(context, lexer)
        return val

    @override
    def __str__(self) -> str:
        return "{" + ", ".join([f"{k}:{v}" for k, v in self.__pairs]) + "}"

class FuncCall(Expr):
    """Function call"""
    def __init__(self, func : Expr, args : list[Expr]):
        self.__func : Expr = func
        self.__args : list[Expr] = args

    @override
    @property
    def tk(self) -> Token:
        return self.__func.tk

    @override
    def value(self, context : Context, lexer : Lexer) -> Any:
        func : Func = None
        if isinstance(self.__func, Term) and self.__func.val == TkType.NAME:
            if not (self.__func.val.content in context.funcs):
                lexer.exception("Unkown function", self.__func.val)
            func : Func = context.funcs[self.__func.val.content]
        elif isinstance(self.__func, Access):
            obj : Any = self.__func.get_obj(context, lexer)
            try:
                method : Callable = getattr(type(obj), self.__func.member.content)
                if not (method in Context.methods): raise Exception()
            except Exception as e:
                lexer.exception(f"Method {self.__func.member.content} not found", self.__func.tk)
            func : BuiltinFunc = BuiltinFunc(self.__func.member.content, Context.methods[method], self.__func.getattr(obj))
        else:
            lexer.exception("Not a function", self.__func.tk)
        args : list[Any] = []
        for x in self.__args:
            if isinstance(x, Unwrap):
                args.extend(x.value(context, lexer))
            else:
                args.append(x.value(context, lexer))
        return func.call(args, self.__func.tk, lexer)

    @override
    def __str__(self) -> str:
        return f"{self.__func.content}({self.__args})"

class Operation(Expr):
    """Binary / unary operation"""

    BIN_OPS : dict[str, Callable] = {
        "+": lambda x, y : x + y,
        "-": lambda x, y : x - y,
        "/": lambda x, y : x / y,
        "%": lambda x, y : x % y,
        "^": lambda x, y : x ** y,
        "|": lambda x, y : x | y,
        "&": lambda x, y : x & y,
        ">": lambda x, y : x > y,
        "<": lambda x, y : x < y,
        ">=": lambda x, y : x >= y,
        "<=": lambda x, y : x <= y,
        "==": lambda x, y : x == y,
        "~=": lambda x, y : math.isclose(x, y, abs_tol=0.0001),
        "!=": lambda x, y : x != y,
        "xor": lambda x, y : (x or y) and x != y,
        "[": lambda x, y : x[y]
    }

    UNARY_OPS : dict[str, Callable] = {
        "-": lambda x : -x,
        "not": lambda x : not x
    }

    def __init__(self, operator : Token, *operands : Expr):
        self.__operator : Token = operator
        self.__operands : tuple[Expr] = operands

    @property
    def operator(self) -> Token:
        return self.__operator

    @override
    @property
    def tk(self) -> Token:
        return self.operator

    @property
    def operands(self) -> tuple[Expr]:
        return self.__operands

    @override
    def value(self, context : Context, lexer : Lexer) -> Any:
        try:
            if self.__operator == "and":
                if not self.__operands[0].value(context, lexer):
                    return False
                return bool(self.__operands[1].value(context, lexer))
            if self.__operator == "or":
                if self.__operands[0].value(context, lexer):
                    return True
                return bool(self.__operands[1].value(context, lexer))
            if len(self.__operands) == 2 and self.__operator.content in self.BIN_OPS:
                return self.BIN_OPS[self.__operator.content](*[x.value(context, lexer) for x in self.__operands])
            elif len(self.__operands) == 1 and self.__operator.content in self.UNARY_OPS:
                return self.UNARY_OPS[self.__operator.content](self.__operands[0].value(context, lexer))
        except Exception as e:
            lexer.exception(f"{type(e).__name__} - {e}", self.__operator)
        lexer.exception(f"Unknown operator {self.__operator.content}", self.__operator)

    @override
    def __str__(self) -> str:
        if len(self.__operands) == 2:
            return f"{self.__operands[0]} {self.__operator.content} {self.__operands[1]}"
        else:
            return f"{self.__operator.content}{self.__operands[0]}"

class Unwrap(Expr):
    """Argument unwrapping of list (*list -> elem1, elem2, elem3, ...)"""
    def __init__(self, operator : Token, elems : Expr):
        self.__op : Token = operator
        self.__elems : Expr = elems

    @override
    @property
    def tk(self) -> Token:
        return self.__operator

    @override
    def value(self, context : Context, lexer : Lexer) -> Any:
        val : list | tuple = self.__elems.value(context, lexer)
        val = val if val else []
        if not isinstance(val, (list, tuple)):
            lexer.exception(f"Cannot unwrap a type other than list, got {type_to_str(type(val))} instead", self.__op)
        return val

    @override
    def __str__(self) -> str:
        return f"*{self.__elems}"

class Access(Expr):
    """Dot operator access (something.something)"""
    def __init__(self, where : Expr, member : Token):
        self.__where : Expr = where
        self.__member : Token = member

    @override
    @property
    def tk(self) -> Token:
        return self.__member

    @property
    def where(self) -> Expr:
        return self.__where

    @property
    def member(self) -> Token:
        return self.__member

    def get_obj(self, context : Context, lexer : Lexer) -> Any:
        return self.__where.value(context, lexer)

    def getattr(self, obj : Any) -> Any:
        try:
            return getattr(obj, self.__member.content)
        except Exception as e:
            if type(e) == Exception:
                raise e
            lexer.exception(f"{type(e).__name__} - {e}", self.__member)

    @override
    def value(self, context : Context, lexer : Lexer) -> Any:
        obj : Any = self.get_obj(context, lexer)
        if not (type(obj) in Context.attributes) or not (self.member.content in Context.attributes[type(obj)]):
            lexer.exception(f"Attribute {self.member.content} not found", self.tk)
        return self.getattr(obj)

    @override
    def __str__(self) -> str:
        return f"{self.__where}.{self.__member}"

class Context:
    """Context necessary for computation of statements and expression.
        Essentially contains the scope's variables and functions."""
    types : dict[str, type | None] = {
        "any" : None,
        "nothing" : Nothing
    }

    methods : dict[callable, list[Arg | Varg]] = {}
    attributes : dict[type, set[str]] = {}

    def __init__(self, vars : dict[str, Var] | None = None, funcs : dict[str, Func] | None = None):
        self.__vars : dict[str, Var] = vars if vars else {}
        self.__funcs : dict[str, Func] = funcs if funcs else {}

    @property
    def vars(self) -> dict[str, Var]:
        return self.__vars

    @property
    def funcs(self) -> dict[str, Func]:
        return self.__funcs

    def __add__(self, other : Context) -> Context:
        if not isinstance(other, Context):
            raise TypeError("other must be a Context")
        ctx = Context(self.vars.copy(), self.funcs.copy())
        for k, v in other.vars.items(): ctx.vars[k] = v
        for k, v in other.funcs.items(): ctx.funcs[k] = v
        return ctx

class Statement:
    def __init__(self, parent : Statement | None = None):
        self.__parent : Statement | None = parent

    @property
    def lexer(self) -> Lexer:
        return self.parent.lexer

    @property
    def parent(self) -> Statement:
        return self.__parent

    @property
    def context(self) -> Context:
        return self.parent.context

    def add_var(self, var : Var) -> bool:
        if self.parent is None: return False
        return self.parent.add_var(var)

    def add_func(self, func : Func) -> bool:
        if self.parent is None: return False
        return self.parent.add_func(func)

    @abstractmethod
    def execute(self) -> Any | None:
        pass

class ExprStatement(Statement):
    def __init__(self, expr : Expr, parent : Statement):
        super().__init__(parent)
        self.__expr : Expr = expr

    @override
    def execute(self):
        self.__expr.value(self.context, self.lexer)

class Return(Statement):
    def __init__(self, expr : Expr, parent : Statement):
        super().__init__(parent)
        self.__expr : Expr = expr

    @override
    def execute(self):
        return self.__expr.value(self.context, self.lexer)

class VarCreation(Statement):
    def __init__(self, name : Token, type : type | tuple[type] | None, value : Expr | None, parent : Statement):
        super().__init__(parent)
        self.__name : Token = name
        self.__type : type | tuple[type] | None = type
        self.__value : Expr | None = value

    @override
    def execute(self):
        var : Var = Var(
            self.__name.content,
            self.__value.value(self.context, self.lexer) if self.__value else Nothing(),
            self.__type,
            self.__name
        )
        if not self.add_var(var):
            self.lexer.exception(f"Could not create variable {self.__name.content}", self.__name)

class VarAssignment(Statement):
    def __init__(self, dest : Expr, value : Expr, parent : Statement):
        super().__init__(parent)
        self.__dest : Expr = dest
        self.__value : Expr = value

    @override
    def execute(self):
        if isinstance(self.__dest, Term) and self.__dest.val == TkType.NAME:
            if not (self.__dest.val.content in self.context.vars):
                self.lexer.exception(f"Variable {self.__dest.val} does not exist", self.__dest.val)
            var : Var = self.context.vars[self.__dest.val.content]
            var.value = self.__value.value(self.context, self.lexer)
        elif isinstance(self.__dest, Operation) and self.__dest.operator == "[":
            l : Any = self.__dest.operands[0].value(self.context, self.lexer)
            idx : Any = self.__dest.operands[1].value(self.context, self.lexer)
            try:
                l[idx] = self.__value.value(self.context, self.lexer)
            except Exception as e:
                if type(e) == Exception:
                    raise e
                self.lexer.exception(f"{type(e).__name__} - {e}", self.__dest.operator)
        else:
            self.lexer.exception(f"Cannot assign value to {self.__dest}", self.__dest.tk)

class Scope(Statement):
    def __init__(self, parent : Statement | None = None):
        super().__init__(parent)
        self.__context : Context = Context()
        self._stmts : list[Statement] = []

    @override
    @property
    def context(self) -> Context:
        if self.parent:
            return self.parent.context + self.__context
        return self.__context

    @override
    def add_var(self, var : Var) -> bool:
        self.__context.vars[var.name] = var
        return True

    @override
    def add_func(self, func : Func) -> bool:
        self.__context.funcs[func.name] = func
        return True

    def add_stmt(self, stmt : Statement):
        self._stmts.append(stmt)

    @override
    def execute(self) -> Any:
        for stmt in self._stmts:
            val = stmt.execute()
            if not (val is None):
                return val

class DefinedFunc(Func):
    def __init__(self, fdef : FuncDef):
        super().__init__(fdef.name.content, fdef.args, fdef.type, fdef.name)
        self.__fdef : FuncDef = fdef

    @override
    def call(self, args : list[Any], where : Token, lexer : Lexer) -> Any:
        args = self.get_args(args, where, lexer)
        for arg in self.args:
            if isinstance(arg, Varg):
                self.__fdef.add_var(Var(arg.name, args, list, arg.definition))
            else:
                self.__fdef.add_var(Var(arg.name, args.pop(0), arg.type, arg.definition))
        val : Any = self.__fdef.call()
        if isinstance(val, LoopInterupt):
            lexer.exception(f"Not inside a loop", val.source)
        if not self.ret_compatible(val):
            lexer.exception(f"Return value {repr(val)} is not compatible with type {type_to_str(self.type)}", self.definition)
        return val

class FuncDef(Scope):
    def __init__(self, name : Token, args : list[Arg | Varg], type : type | tuple[type] | None, parent : Statement):
        super().__init__(parent)
        self.__name : Token = name
        self.__args : list[Arg | Varg] = args
        self.__type : type | tuple[type] | None = type

    @property
    def name(self) -> Token:
        return self.__name
    @property
    def args(self) -> list[Arg | Varg]:
        return self.__args
    @property
    def type(self) -> type | tuple[type] | None:
        return self.__type

    @override
    def execute(self):
        func : Func = DefinedFunc(self)
        if not self.parent.add_func(func):
            self.lexer.exception(f"Could not create function {self.__name.content}", self.__name)

    def call(self) -> Any:
        val = super().execute()
        if val is None:
            return Nothing()
        return val

class ControlFlow(Statement, ABC):
    def __init__(self, parent : Statement):
        super().__init__(parent)
        self._stmts : list[Statement] = []

    def add_stmt(self, stmt : Statement):
        self._stmts.append(stmt)

    def _execute_stmts(self) -> Any:
        for stmt in self._stmts:
            val = stmt.execute()
            if not (val is None):
                return val

class If(ControlFlow):
    def __init__(self, condition : Expr, parent : Statement):
        super().__init__(parent)
        self._cond : Expr = condition
        self._condition : bool = False

    @property
    def condition(self) -> bool:
        return self._condition

    @override
    def execute(self):
        if self._cond.value(self.context, self.lexer):
            self._condition = True
            return self._execute_stmts()
        self._condition = False

class Elif(If):
    def __init__(self, condition : Expr, last : If | Elif, parent : Statement):
        super().__init__(condition, parent)
        self.__last : If | Elif = last

    @override
    def execute(self):
        if self.__last.condition:
            self._condition = True
            return
        return super().execute()

class Else(ControlFlow):
    def __init__(self, last : If | Elif, parent : Statement):
        super().__init__(parent)
        self.__last : If | Elif = last

    @override
    def execute(self):
        if not self.__last.condition:
            return self._execute_stmts()

class LoopInterupt(Statement, ABC):
    def __init__(self, source : Token, parent : Statement):
        super().__init__(parent)
        self.__source : Token = source

    @property
    def source(self) -> Token:
        return self.__source

    @override
    def execute(self) -> LoopInterupt:
        return self

class Break(LoopInterupt):
    pass

class Continue(LoopInterupt):
    pass

class While(ControlFlow):
    def __init__(self, condition : Expr, parent : Statement):
        super().__init__(parent)
        self.__condition : Expr = condition

    @override
    def execute(self):
        while self.__condition.value(self.context, self.lexer):
            val : Any = self._execute_stmts()
            if not (val is None):
                if isinstance(val, Break): break
                elif isinstance(val, Continue): continue
                return val

class ForIter(ControlFlow):
    def __init__(self, elems : list[Token], iterator : Expr, parent : Statement):
        super().__init__(parent)
        self.__elems : list[Token] = elems
        self.__iterator : Expr = iterator

    @override
    def execute(self):
        iterator : Any = self.__iterator.value(self.context, self.lexer).copy()
        vars : list[Var] = [Var(elem.content, definition=elem) for elem in self.__elems]
        for v in vars: self.add_var(v)
        if len(self.__elems) == 1:
            for x in iterator:
                vars[0].value = x
                val : Any = self._execute_stmts()
                if not (val is None):
                    if isinstance(val, Break): break
                    elif isinstance(val, Continue): continue
                    return val
        elif len(self.__elems) == 2:
            for x, y in iterator:
                vars[0].value = x
                vars[1].value = y
                val : Any = self._execute_stmts()
                if not (val is None):
                    if isinstance(val, Break): break
                    elif isinstance(val, Continue): continue
                    return val

class ForStep(ControlFlow):
    def __init__(self, var : Token, start : Expr, end : Expr, step : Expr, parent : Statement):
        super().__init__(parent)
        self.__var : Token = var
        self.__start : Expr = start
        self.__end : Expr = end
        self.__step : Expr = step

    @override
    def execute(self):
        v : Var = Var(self.__var.content, type=(int, float), definition=self.__var)
        self.add_var(v)
        v.value = self.__start.value(self.context, self.lexer)
        while True:
            end : Any = self.__end.value(self.context, self.lexer)
            step : Any = self.__step.value(self.context, self.lexer)
            v.value += step
            if not isinstance(end, (int, float)):
                self.lexer.exception("Expected int or float value for end", self.__end.tk)
            if step == 0 or (step > 0 and v.value > end) or (step < 0 and v.value < end):
                break
            val : Any = self._execute_stmts()
            if not (val is None):
                if isinstance(val, Break): break
                elif isinstance(val, Continue): continue
                return val

class GlobalScope(Scope):
    builtins : list[BuiltinFunc] = []

    def __init__(self, lexer : Lexer):
        super().__init__()
        for f in self.builtins:
            self.context.funcs[f.name] = f
        self.__lexer : Lexer = lexer

    @override
    @property
    def lexer(self) -> Lexer:
        return self.__lexer

    @override
    def execute(self):
        val = super().execute()
        if isinstance(val, LoopInterupt):
            self.lexer.exception(f"Not inside a loop", val.source)
        return val
