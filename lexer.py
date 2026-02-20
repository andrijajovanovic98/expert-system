#!/usr/bin/env python3
# *************************************************************************** #
#                                                                             #
#                                                        :::      ::::::::    #
#   lexer.py                                           :+:      :+:    :+:    #
#                                                    +:+ +:+         +:+      #
#   By: iberegsz <iberegsz@student.42vienna.com>   +#+  +:+       +#+         #
#                                                +#+#+#+#+#+   +#+            #
#   Created: 2025/10/22 11:20:48 by iberegsz          #+#    #+#              #
#   Updated: 2026/01/19 19:16:52 by iberegsz         ###   ########.fr        #
#                                                                             #
# *************************************************************************** #

"""Lexer for the expert system input language.

Tokenizes input files according to the project specification.
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Optional


class TokenType(Enum):
    """Token types for the expert system language."""
    LPAREN = auto()      # (
    RPAREN = auto()      # )
    NOT = auto()         # !
    AND = auto()         # +
    OR = auto()          # |
    XOR = auto()         # ^
    IMPLIES = auto()     # =>
    IFF = auto()         # <=>

    FACT = auto()        # A-Z
    EQUALS = auto()      # =
    QUERY = auto()       # ?
    NEWLINE = auto()
    EOF = auto()
    COMMENT = auto()     # #


@dataclass(frozen=True)
class Token:
    """Represents a token in the input."""
    type: TokenType
    value: str
    line: int
    column: int

    def __repr__(self):
        parts = (
            "Token(",
            self.type.name,
            ", ",
            repr(self.value),
            ", L",
            str(self.line),
            ":C",
            str(self.column),
            ")",
        )
        return "".join(parts)


class Lexer:
    """Tokenizes input according to expert system language rules."""

    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []

    def current_char(self) -> Optional[str]:
        """Get current character without advancing."""
        if self.pos >= len(self.text):
            return None
        return self.text[self.pos]

    def peek_char(self, offset: int = 1) -> Optional[str]:
        """Look ahead at character without advancing."""
        pos = self.pos + offset
        if pos >= len(self.text):
            return None
        return self.text[pos]

    def advance(self) -> Optional[str]:
        """Move to next character and return current."""
        if self.pos >= len(self.text):
            return None

        char = self.text[self.pos]
        self.pos += 1

        if char == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1

        return char

    def skip_whitespace(self, skip_newlines: bool = True):
        """Skip whitespace characters."""
        while self.current_char() is not None:
            if self.current_char() == '\n' and not skip_newlines:
                break
            if self.current_char() in ' \t\r\n':
                self.advance()
            else:
                break

    def skip_comment(self):
        """Skip comment line (from # to end of line)."""
        if self.current_char() == '#':
            while True:
                ch = self.current_char()
                if ch is None or ch == '\n':
                    break
                self.advance()

    def make_token(self, token_type: TokenType, value: str) -> Token:
        """Create a token at current position."""
        return Token(token_type, value, self.line, self.column - len(value))

    def tokenize(self) -> List[Token]:
        """Tokenize the entire input."""
        self.tokens = []

        while self.current_char() is not None:
            if self.current_char() in ' \t\r':
                self.advance()
                continue

            if self.current_char() == '\n':
                self.advance()
                continue

            if self.current_char() == '#':
                self.skip_comment()
                continue

            if self.current_char() == '(':
                tok = self.make_token(TokenType.LPAREN, '(')
                self.tokens.append(tok)
                self.advance()
                continue

            if self.current_char() == ')':
                tok = self.make_token(TokenType.RPAREN, ')')
                self.tokens.append(tok)
                self.advance()
                continue

            if self.current_char() == '!':
                tok = self.make_token(TokenType.NOT, '!')
                self.tokens.append(tok)
                self.advance()
                continue

            if self.current_char() == '+':
                tok = self.make_token(TokenType.AND, '+')
                self.tokens.append(tok)
                self.advance()
                continue

            if self.current_char() == '|':
                tok = self.make_token(TokenType.OR, '|')
                self.tokens.append(tok)
                self.advance()
                continue

            if self.current_char() == '^':
                tok = self.make_token(TokenType.XOR, '^')
                self.tokens.append(tok)
                self.advance()
                continue

            if self.current_char() == '<':
                start_col = self.column
                self.advance()
                if self.current_char() == '=' and self.peek_char() == '>':
                    self.advance()
                    self.advance()
                    self.tokens.append(
                        Token(
                            TokenType.IFF,
                            '<=>',
                            self.line,
                            start_col,
                        )
                    )
                else:
                    raise SyntaxError(
                        f"Invalid character '<' at line {self.line}, "
                        f"column {start_col}"
                    )
                continue

            if self.current_char() == '=':
                start_col = self.column
                self.advance()
                if self.current_char() == '>':
                    self.advance()
                    self.tokens.append(
                        Token(
                            TokenType.IMPLIES,
                            '=>',
                            self.line,
                            start_col,
                        )
                    )
                else:
                    self.tokens.append(
                        Token(
                            TokenType.EQUALS,
                            '=',
                            self.line,
                            start_col,
                        )
                    )
                continue

            if self.current_char() == '?':
                tok = self.make_token(TokenType.QUERY, '?')
                self.tokens.append(tok)
                self.advance()
                continue

            if self.current_char().isupper():
                fact = self.current_char()
                tok = self.make_token(TokenType.FACT, fact)
                self.tokens.append(tok)
                self.advance()
                continue

            msg = (
                "Unexpected character '"
                + str(self.current_char())
                + f"' at line {self.line}, column {self.column}"
            )
            raise SyntaxError(msg)

        self.tokens.append(Token(TokenType.EOF, '', self.line, self.column))
        return self.tokens
