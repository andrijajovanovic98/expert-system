#!/usr/bin/env python3
# *************************************************************************** #
#                                                                             #
#                                                        :::      ::::::::    #
#   parser.py                                          :+:      :+:    :+:    #
#                                                    +:+ +:+         +:+      #
#   By: iberegsz <iberegsz@student.42vienna.com>   +#+  +:+       +#+         #
#                                                +#+#+#+#+#+   +#+            #
#   Created: 2025/10/22 11:21:36 by iberegsz          #+#    #+#              #
#   Updated: 2026/01/19 19:17:09 by iberegsz         ###   ########.fr        #
#                                                                             #
# *************************************************************************** #

"""Parser for the expert system input language.

Builds an Abstract Syntax Tree (AST) from tokens and respects
operator precedence: (), !, +, |, ^, =>, <=>
"""

import sys
from dataclasses import dataclass
from typing import List, Set
from enum import Enum, auto
from lexer import Token, TokenType, Lexer


class NodeType(Enum):
    """Types of AST nodes."""
    FACT = auto()
    NOT = auto()
    AND = auto()
    OR = auto()
    XOR = auto()
    IMPLIES = auto()
    IFF = auto()


@dataclass
class ASTNode:
    """Base class for AST nodes."""
    node_type: NodeType

    def get_facts(self) -> Set[str]:
        """Get all facts referenced in this node."""
        raise NotImplementedError


@dataclass
class FactNode(ASTNode):
    """Represents a single fact (A-Z)."""
    fact: str

    def __init__(self, fact: str):
        super().__init__(NodeType.FACT)
        self.fact = fact

    def get_facts(self) -> Set[str]:
        return {self.fact}

    def __repr__(self):
        return f"Fact({self.fact})"


@dataclass
class UnaryOpNode(ASTNode):
    """Represents a unary operation (NOT)."""
    operand: ASTNode

    def __init__(self, node_type: NodeType, operand: ASTNode):
        super().__init__(node_type)
        self.operand = operand

    def get_facts(self) -> Set[str]:
        return self.operand.get_facts()

    def __repr__(self):
        return f"{self.node_type.name}({self.operand})"


@dataclass
class BinaryOpNode(ASTNode):
    """Represents a binary operation (AND, OR, XOR, IMPLIES, IFF)."""
    left: ASTNode
    right: ASTNode

    def __init__(self, node_type: NodeType, left: ASTNode, right: ASTNode):
        super().__init__(node_type)
        self.left = left
        self.right = right

    def get_facts(self) -> Set[str]:
        return self.left.get_facts() | self.right.get_facts()

    def __repr__(self):
        return f"{self.node_type.name}({self.left}, {self.right})"


@dataclass
class Rule:
    """
    Represents a rule: condition => conclusion or condition <=> conclusion.
    """
    condition: ASTNode
    conclusion: ASTNode
    is_biconditional: bool = False

    def get_all_facts(self) -> Set[str]:
        """Get all facts used in this rule."""
        return self.condition.get_facts() | self.conclusion.get_facts()

    def __repr__(self):
        op = "<=>" if self.is_biconditional else "=>"
        return (
            "Rule(" + repr(self.condition) + " " + op + " "
            + repr(self.conclusion) + ")"
        )


class Parser:
    """Parses tokens into an AST.

    Grammar (lowest to highest precedence):
    rule    -> iff
    iff     -> implies ('<=>' implies)*
    implies -> or ('=>' or)*
    or      -> xor ('|' xor)*
    xor     -> and ('^' and)*
    and     -> not ('+' not)*
    not     -> '!' not | primary
    primary -> '(' iff ')' | FACT
    """

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def current_token(self) -> Token:
        """Get current token."""
        if self.pos >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[self.pos]

    def peek_token(self, offset: int = 1) -> Token:
        """Look ahead at token."""
        pos = self.pos + offset
        if pos >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[pos]

    def advance(self) -> Token:
        """Move to next token and return current."""
        token = self.current_token()
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return token

    def expect(self, token_type: TokenType) -> Token:
        """Consume a token of expected type or raise SyntaxError."""
        token = self.current_token()
        if token.type != token_type:
            raise SyntaxError(
                f"Expected {token_type.name}, got {token.type.name} "
                f"at line {token.line}, column {token.column}"
            )
        self.advance()
        return token

    def parse_primary(self) -> ASTNode:
        """Parse primary expression: '(' expression ')' | FACT"""
        token = self.current_token()

        if token.type == TokenType.LPAREN:
            self.advance()
            node = self.parse_iff()
            self.expect(TokenType.RPAREN)
            return node

        if token.type == TokenType.FACT:
            self.advance()
            return FactNode(token.value)

        raise SyntaxError(
            f"Expected '(' or FACT, got {token.type.name} "
            f"at line {token.line}, column {token.column}"
        )

    def parse_not(self) -> ASTNode:
        """Parse NOT expression: '!' not | primary"""
        token = self.current_token()

        if token.type == TokenType.NOT:
            self.advance()
            operand = self.parse_not()
            return UnaryOpNode(NodeType.NOT, operand)

        return self.parse_primary()

    def parse_and(self) -> ASTNode:
        """Parse AND expression: not ( '+' not )*"""
        left = self.parse_not()

        while self.current_token().type == TokenType.AND:
            self.advance()
            right = self.parse_not()
            left = BinaryOpNode(NodeType.AND, left, right)

        return left

    def parse_xor(self) -> ASTNode:
        """Parse XOR expression: and ( '^' and )*"""
        left = self.parse_and()

        while self.current_token().type == TokenType.XOR:
            self.advance()
            right = self.parse_and()
            left = BinaryOpNode(NodeType.XOR, left, right)

        return left

    def parse_or(self) -> ASTNode:
        """Parse OR expression: xor ( '|' xor )*"""
        left = self.parse_xor()

        while self.current_token().type == TokenType.OR:
            self.advance()
            right = self.parse_xor()
            left = BinaryOpNode(NodeType.OR, left, right)

        return left

    def parse_implies(self) -> ASTNode:
        """Parse IMPLIES expression: or ( '=>' or )*"""
        left = self.parse_or()

        while self.current_token().type == TokenType.IMPLIES:
            self.advance()
            right = self.parse_or()
            left = BinaryOpNode(NodeType.IMPLIES, left, right)

        return left

    def parse_iff(self) -> ASTNode:
        """Parse IFF expression: implies ( '<=>' implies )*"""
        left = self.parse_implies()

        while self.current_token().type == TokenType.IFF:
            self.advance()
            right = self.parse_implies()
            left = BinaryOpNode(NodeType.IFF, left, right)

        return left

    def parse_expression(self) -> ASTNode:
        """Parse a complete expression."""
        return self.parse_iff()

    def parse_rule(self) -> Rule:
        """Parse a rule: expression (=> | <=>) expression"""
        expr = self.parse_iff()

        if isinstance(expr, BinaryOpNode):
            if expr.node_type == NodeType.IMPLIES:
                return Rule(expr.left, expr.right, is_biconditional=False)
            elif expr.node_type == NodeType.IFF:
                return Rule(expr.left, expr.right, is_biconditional=True)

        raise SyntaxError(
            f"Expected a rule with '=>' or '<=>', but got expression: {expr}")


def parse_input_file(text: str) -> tuple[List[Rule], Set[str], List[str]]:
    """
    Parse the entire input file.
    Returns: (rules, initial_facts, queries)

    Strategy: Parse line by line. Each line can be:
    - A rule (contains => or <=>)
    - Initial facts (starts with =)
    - Queries (starts with ?)
    - Comment (starts with #)
    - Empty line
    """
    rules: List[Rule] = []
    initial_facts: Set[str] = set()
    queries: List[str] = []

    for line_num, line in enumerate(text.split('\n'), 1):
        if '#' in line:
            line = line[:line.index('#')]

        line = line.strip()

        if not line:
            continue

        if line.startswith('='):
            facts_str = line[1:].strip()
            lexer = Lexer(facts_str)
            tokens = lexer.tokenize()
            for token in tokens:
                if token.type == TokenType.FACT:
                    initial_facts.add(token.value)

        elif line.startswith('?'):
            queries_str = line[1:].strip()
            lexer = Lexer(queries_str)
            tokens = lexer.tokenize()
            for token in tokens:
                if token.type == TokenType.FACT:
                    queries.append(token.value)

        else:
            try:
                lexer = Lexer(line)
                tokens = lexer.tokenize()

                has_implies = any(
                    t.type in [
                        TokenType.IMPLIES,
                        TokenType.IFF] for t in tokens)

                if has_implies and len(tokens) > 2:
                    parser = Parser(tokens)
                    rule = parser.parse_rule()
                    rules.append(rule)
            except (SyntaxError, Exception) as e:
                print(
                    f"Warning: Could not parse line {line_num}: {line}",
                    file=sys.stderr)
                print(f"  Error: {e}", file=sys.stderr)

    return rules, initial_facts, queries
