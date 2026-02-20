#!/usr/bin/env python3
# *************************************************************************** #
#                                                                             #
#                                                        :::      ::::::::    #
#   inference_engine.py                                :+:      :+:    :+:    #
#                                                    +:+ +:+         +:+      #
#   By: iberegsz <iberegsz@student.42vienna.com>   +#+  +:+       +#+         #
#                                                +#+#+#+#+#+   +#+            #
#   Created: 2025/10/22 11:10:01 by iberegsz          #+#    #+#              #
#   Updated: 2026/01/19 19:15:03 by iberegsz         ###   ########.fr        #
#                                                                             #
# *************************************************************************** #

"""
Backward-chaining inference engine for the expert system.
Determines if queries are true, false, or undetermined based
on rules and facts.
"""

from typing import Set, Dict, List
from enum import Enum, auto
from parser import Rule, ASTNode, NodeType, FactNode, UnaryOpNode, BinaryOpNode
from knowledge_graph import KnowledgeGraph


class TruthValue(Enum):
    """Possible truth values for facts."""
    TRUE = auto()
    FALSE = auto()
    UNDETERMINED = auto()

    def __repr__(self):
        return self.name


class InferenceEngine:
    """
    Backward-chaining inference engine.

    The engine uses backward chaining to determine the truth
    value of queries:
    1. Start with the query fact
    2. Check if it's in initial facts (TRUE) or can be derived from rules
    3. Recursively evaluate rule conditions
    4. Handle contradictions and undetermined states

    Data Structure (Level 5):
    Uses a global knowledge graph with explicit fact nodes and rule nodes:
    - FactGraphNode: represents facts with bidirectional links to rules
    - RuleGraphNode: represents rules with links to condition/conclusion facts
    - O(1) lookup for rules concluding a fact
    - O(1) lookup for facts used in conditions
    - Graph traversal for proofs and dependency analysis
    """

    def __init__(self, rules: List[Rule], initial_facts: Set[str]):
        self.rules = rules
        self.initial_facts = initial_facts

        self.knowledge_graph = KnowledgeGraph(rules, initial_facts)

        self.cache: Dict[str, TruthValue] = {}

        self.evaluating: Set[str] = set()

        self.all_facts: Set[str] = self.knowledge_graph.get_all_facts()

        self.rules_concluding: Dict[str, List[Rule]] = {}
        self._index_rules()

    def _index_rules(self):
        """
        Build legacy index from knowledge graph for backward compatibility.

        The knowledge graph already maintains this information via
        FactGraphNode.concluding_rules, but we keep this index for
        compatibility with existing code that uses rules_concluding dict.
        """
        for fact_name, fact_node in self.knowledge_graph.fact_nodes.items():
            if fact_node.concluding_rules:
                self.rules_concluding[fact_name] = [
                    rule_node.rule for rule_node in fact_node.concluding_rules
                ]

    def _get_concluded_facts(self, node: ASTNode) -> Set[str]:
        """
        Get all facts that can be directly concluded from a conclusion node.
        For AND conclusions (A + B), returns both A and B.
        For OR/XOR conclusions (A | B, A ^ B), returns both A and B.
        For simple facts, returns just that fact.
        For NOT, returns the negated fact.
        """
        if isinstance(node, FactNode):
            return {node.fact}
        elif isinstance(node, UnaryOpNode) and node.node_type == NodeType.NOT:
            if isinstance(node.operand, FactNode):
                return {f"!{node.operand.fact}"}
            return set()
        elif isinstance(node, BinaryOpNode):
            if node.node_type in (NodeType.AND, NodeType.OR, NodeType.XOR):
                return self._get_concluded_facts(
                    node.left) | self._get_concluded_facts(
                    node.right)
        return set()

    def query(self, fact: str) -> TruthValue:
        """
        Determine the truth value of a fact using backward chaining.
        Returns: TRUE, FALSE, or UNDETERMINED
        """
        if fact in self.cache:
            return self.cache[fact]

        if fact in self.evaluating:
            return TruthValue.UNDETERMINED

        self.evaluating.add(fact)

        try:
            result = self._evaluate_fact(fact)
            if result != TruthValue.UNDETERMINED:
                self.cache[fact] = result
            return result
        finally:
            self.evaluating.discard(fact)

    def _evaluate_fact(self, fact: str) -> TruthValue:
        """Evaluate a single fact."""
        if fact in self.initial_facts:
            return TruthValue.TRUE

        has_fact = fact in self.rules_concluding
        has_negation = f"!{fact}" in self.rules_concluding
        if not has_fact and not has_negation:
            return TruthValue.FALSE

        can_be_true = False
        is_undetermined = False

        if fact in self.rules_concluding:
            for rule in self.rules_concluding[fact]:
                condition_value = self._evaluate_expression(rule.condition)

                if condition_value == TruthValue.TRUE:
                    conclusion_value = self._check_conclusion_for_fact(
                        rule.conclusion, fact)
                    if conclusion_value == TruthValue.TRUE:
                        can_be_true = True
                    elif conclusion_value == TruthValue.UNDETERMINED:
                        is_undetermined = True
                elif condition_value == TruthValue.UNDETERMINED:
                    is_undetermined = True

        negated_fact = f"!{fact}"
        if negated_fact in self.rules_concluding:
            for rule in self.rules_concluding[negated_fact]:
                condition_value = self._evaluate_expression(rule.condition)

                if condition_value == TruthValue.TRUE:
                    if can_be_true:
                        return TruthValue.UNDETERMINED
                elif condition_value == TruthValue.UNDETERMINED:
                    is_undetermined = True

        if can_be_true:
            return TruthValue.TRUE
        elif is_undetermined:
            return TruthValue.UNDETERMINED
        else:
            return TruthValue.FALSE

    def _check_conclusion_for_fact(
        self,
        conclusion: ASTNode,
        fact: str,
    ) -> TruthValue:
        """
        Check if a conclusion node makes a specific fact true.
        Used for complex conclusions like A + B, A | B, or A ^ B.
        """
        if isinstance(conclusion, FactNode):
            if conclusion.fact == fact:
                return TruthValue.TRUE
            return TruthValue.FALSE
        elif isinstance(conclusion, UnaryOpNode):
            if conclusion.node_type == NodeType.NOT:
                if isinstance(conclusion.operand, FactNode):
                    if conclusion.operand.fact == fact:
                        return TruthValue.FALSE
                    return TruthValue.FALSE
                return TruthValue.UNDETERMINED
        elif isinstance(conclusion, BinaryOpNode):
            if conclusion.node_type == NodeType.AND:
                left_result = self._check_conclusion_for_fact(
                    conclusion.left, fact
                )
                right_result = self._check_conclusion_for_fact(
                    conclusion.right, fact
                )

                if (
                    left_result == TruthValue.TRUE
                    or right_result == TruthValue.TRUE
                ):
                    return TruthValue.TRUE

                return TruthValue.FALSE
            elif conclusion.node_type == NodeType.OR:
                left_result = self._check_conclusion_for_fact(
                    conclusion.left, fact
                )
                right_result = self._check_conclusion_for_fact(
                    conclusion.right, fact
                )

                if (
                    left_result == TruthValue.TRUE
                    or right_result == TruthValue.TRUE
                ):
                    return TruthValue.UNDETERMINED

                return TruthValue.FALSE
            elif conclusion.node_type == NodeType.XOR:
                left_result = self._check_conclusion_for_fact(
                    conclusion.left, fact
                )
                right_result = self._check_conclusion_for_fact(
                    conclusion.right, fact
                )

                if (
                    left_result == TruthValue.TRUE
                    or right_result == TruthValue.TRUE
                ):
                    return TruthValue.UNDETERMINED

                return TruthValue.FALSE

        return TruthValue.UNDETERMINED

    def _evaluate_expression(self, node: ASTNode) -> TruthValue:
        """Evaluate a logical expression to TRUE, FALSE, or UNDETERMINED."""
        if isinstance(node, FactNode):
            return self.query(node.fact)

        elif isinstance(node, UnaryOpNode):
            if node.node_type == NodeType.NOT:
                operand_value = self._evaluate_expression(node.operand)
                if operand_value == TruthValue.TRUE:
                    return TruthValue.FALSE
                elif operand_value == TruthValue.FALSE:
                    return TruthValue.TRUE
                else:
                    return TruthValue.UNDETERMINED

        elif isinstance(node, BinaryOpNode):
            left_value = self._evaluate_expression(node.left)
            right_value = self._evaluate_expression(node.right)

            if node.node_type == NodeType.AND:
                return self._eval_and(left_value, right_value)
            elif node.node_type == NodeType.OR:
                return self._eval_or(left_value, right_value)
            elif node.node_type == NodeType.XOR:
                return self._eval_xor(left_value, right_value)
            elif node.node_type == NodeType.IMPLIES:
                return self._eval_implies(left_value, right_value)
            elif node.node_type == NodeType.IFF:
                return self._eval_iff(left_value, right_value)

        return TruthValue.UNDETERMINED

    def _eval_and(self, left: TruthValue, right: TruthValue) -> TruthValue:
        """Evaluate AND operation."""
        if left == TruthValue.FALSE or right == TruthValue.FALSE:
            return TruthValue.FALSE
        elif left == TruthValue.TRUE and right == TruthValue.TRUE:
            return TruthValue.TRUE
        else:
            return TruthValue.UNDETERMINED

    def _eval_or(self, left: TruthValue, right: TruthValue) -> TruthValue:
        """Evaluate OR operation."""
        if left == TruthValue.TRUE or right == TruthValue.TRUE:
            return TruthValue.TRUE
        elif left == TruthValue.FALSE and right == TruthValue.FALSE:
            return TruthValue.FALSE
        else:
            return TruthValue.UNDETERMINED

    def _eval_xor(self, left: TruthValue, right: TruthValue) -> TruthValue:
        """Evaluate XOR (exclusive OR) operation."""
        if left == TruthValue.UNDETERMINED or right == TruthValue.UNDETERMINED:
            return TruthValue.UNDETERMINED
        elif (
            (left == TruthValue.TRUE and right == TruthValue.FALSE)
            or (left == TruthValue.FALSE and right == TruthValue.TRUE)
        ):
            return TruthValue.TRUE
        else:
            return TruthValue.FALSE

    def _eval_implies(self, left: TruthValue, right: TruthValue) -> TruthValue:
        """
        Evaluate IMPLIES operation (A => B).
        True if: left is false OR right is true
        False if: left is true AND right is false
        """
        if left == TruthValue.FALSE:
            return TruthValue.TRUE
        elif left == TruthValue.TRUE:
            return right
        else:
            if right == TruthValue.TRUE:
                return TruthValue.TRUE
            else:
                return TruthValue.UNDETERMINED

    def _eval_iff(self, left: TruthValue, right: TruthValue) -> TruthValue:
        """
        Evaluate IFF (if and only if) operation (A <=> B).
        True if: both are true OR both are false
        False if: one is true and the other is false
        """
        if left == TruthValue.UNDETERMINED or right == TruthValue.UNDETERMINED:
            return TruthValue.UNDETERMINED
        elif left == right:
            return TruthValue.TRUE
        else:
            return TruthValue.FALSE

    def query_all(self, queries: List[str]) -> Dict[str, TruthValue]:
        """Query multiple facts and return results."""
        results = {}
        for query in queries:
            results[query] = self.query(query)
        return results

    def reset_cache(self):
        """Clear the cache and evaluation state."""
        self.cache.clear()
        self.evaluating.clear()
