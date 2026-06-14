from __future__ import annotations
from typing import Any
from types import NoneType
from enum import Enum

import re

"""
This module's job is to transform raw text into individual words, numbers and symbols.
"""

class TkType(Enum):
    """The type of a Token."""
    NAME        = 0
    NUMBER      = 1
    STRING      = 2
    TRUE        = 3
    FALSE       = 4
    NOTHING     = 5
    OPERATOR    = 6

class Token:
    def __init__(self, content : str, type : TkType, line : int, offset : int = 0):
        self.__content : str = content
        self.__type : TkType = type
        self.__line : int = line
        self.__offset : int = offset

    @property
    def content(self) -> str:
        return self.__content

    @property
    def type(self) -> TkType:
        return self.__type

    @property
    def line(self) -> int:
        return self.__line

    @property
    def offset(self) -> int:
        return self.__offset

    def __repr__(self) -> str:
        return f"Token({self.content}, {self.type})"

    def __str__(self) -> str:
        return self.content

    def __eq__(self, o : Any) -> bool:
        if isinstance(o, str):
            return self.content == o
        elif isinstance(o, TkType):
            return self.type == o
        return False


class Lexer:
    SPACE : re.Pattern    = re.compile(r"\s+")
    NAME : re.Pattern     = re.compile(r"[a-zA-Z_][a-zA-Z_0-9]*")
    NUMBER : re.Pattern   = re.compile(r"0x[0-9a-fA-F]+|0o[0-7]+|0b[01]+|[0-9]+(?:\.[0-9]+)?(?:e[+-]?[0-9]+)?")
    STRING : re.Pattern   = re.compile(r"\"[^\"]*\"")
    OPERATOR : re.Pattern = re.compile(r"[><]{2}|[><]=?|[!=~]?=|[\+\-\*/%&\|\^]=?|[\[\]\{\}\(\).,:;]")
    CONSTS : dict[str, TkType] = {"true": TkType.TRUE, "yes": TkType.TRUE,
                                  "false": TkType.FALSE, "no": TkType.FALSE,
                                  "nothing": TkType.NOTHING, "none": TkType.NOTHING}
    LOGIC_OPS : set[str] = {"and", "or", "xor", "not"}

    def __init__(self, program : str, name : str = ""):
        if not isinstance(program, str) or not isinstance(name, str):
            raise TypeError("program and name must be str")
        self.__name : str = name
        self.__program : list[str] = program.expandtabs(4).splitlines()
        self.__tokens : list[Token] = []

    @property
    def name(self) -> str:
        return self.__name

    @property
    def tokens(self) -> list[Token]:
        return self.__tokens

    def get_context(self, line : int, offset : int = None, msg : str = "") -> str:
        if not isinstance(line, int) or not isinstance(offset, (int, NoneType)) or not isinstance(msg, str):
            raise TypeError("line and offset must be an int; msg must be str")
        text : str = f"{self.name} (line {line})"
        if msg: text += f" : {msg}"
        line_head : str = f"\n{line : >4d} | "
        text += line_head + self.__program[line-1]
        if offset != None:
            text += "\n" +" " * (len(line_head) + offset - 1) + "^"
        return text

    def exception(self, msg : str, tk : Token | int | tuple) -> Exception:
        if not isinstance(msg, str) or not isinstance(tk, (Token, int, tuple)):
            raise TypeError("msg must be str; tk must be a Token")
        if isinstance(tk, Token):
            raise Exception(self.get_context(tk.line, tk.offset, msg))
        elif isinstance(tk, int):
            raise Exception(self.get_context(tk, msg=msg))
        else:
            raise Exception(self.get_context(*tk, msg=msg))

    def tokenize(self) -> Lexer:
        if self.tokens: raise ValueError("Program was already tokenized!")
        line_number : int = 1
        for line in self.__program:
            offset : int = 0
            while line:
                match : re.Match | None = None
                if (match := self.SPACE.match(line)) is not None:
                    pass
                elif (match := self.OPERATOR.match(line)) is not None:
                    self.tokens.append(Token(match.group(0), TkType.OPERATOR, line_number, offset))
                elif (match := self.NUMBER.match(line)) is not None:
                    self.tokens.append(Token(match.group(0), TkType.NUMBER, line_number, offset))
                elif (match := self.STRING.match(line)) is not None:
                    self.tokens.append(Token(match.group(0), TkType.STRING, line_number, offset))
                elif (match := self.NAME.match(line)) is not None:
                    name : str = match.group(0)
                    type : TkType = TkType.NAME
                    if name in self.CONSTS:
                        type = self.CONSTS[name]
                    elif name in self.LOGIC_OPS:
                        type = TkType.OPERATOR
                    self.tokens.append(Token(name, type, line_number, offset))
                elif line.startswith("#"):
                    line_number += 1
                    break
                else:
                    self.exception(f"Unknown symbol '{line[0]}'", (line_number, offset))
                line = line[match.end():]
                offset += match.end()
            line_number += 1
        return self
