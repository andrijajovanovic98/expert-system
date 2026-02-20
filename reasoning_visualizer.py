#!/usr/bin/env python3
# *************************************************************************** #
#                                                                             #
#                                                        :::      ::::::::    #
#   reasoning_visualizer.py                            :+:      :+:    :+:    #
#                                                    +:+ +:+         +:+      #
#   By: iberegsz <iberegsz@student.42vienna.com>   +#+  +:+       +#+         #
#                                                +#+#+#+#+#+   +#+            #
#   Created: 2026/01/18 21:17:16 by iberegsz          #+#    #+#              #
#   Updated: 2026/01/19 16:04:07 by iberegsz         ###   ########.fr        #
#                                                                             #
# *************************************************************************** #

"""
Reasoning Visualization (Bonus Feature #2)

Provides detailed feedback explaining why a fact is true, false, or
undetermined, showing the full reasoning chain in natural language
and formal logic notation.
"""

import sys
from pathlib import Path
from parser import (
    parse_input_file, NodeType, FactNode,
    UnaryOpNode, BinaryOpNode
)
from inference_engine import InferenceEngine, TruthValue


class ReasoningVisualizer:
    """Visualizes the reasoning process for queries."""

    def __init__(self, rules, initial_facts):
        self.rules = rules
        self.initial_facts = initial_facts
        self.engine = InferenceEngine(rules, initial_facts)
        self.reasoning_steps = []
        self.depth = 0

    def format_node(self, node):
        """Format an AST node as a string."""
        if isinstance(node, FactNode):
            return node.fact
        elif isinstance(node, UnaryOpNode):
            if node.node_type == NodeType.NOT:
                operand = self.format_node(node.operand)
                return f"¬{operand}"
        elif isinstance(node, BinaryOpNode):
            left = self.format_node(node.left)
            right = self.format_node(node.right)
            op_map = {
                NodeType.AND: "∧",
                NodeType.OR: "∨",
                NodeType.XOR: "⊕",
                NodeType.IMPLIES: "⇒",
                NodeType.IFF: "⇔"
            }
            op = op_map.get(node.node_type, "?")
            return f"({left} {op} {right})"
        return "?"

    def format_node_natural(self, node):
        """Format an AST node in natural language."""
        if isinstance(node, FactNode):
            return node.fact
        elif isinstance(node, UnaryOpNode):
            if node.node_type == NodeType.NOT:
                operand = self.format_node_natural(node.operand)
                return f"NOT {operand}"
        elif isinstance(node, BinaryOpNode):
            left = self.format_node_natural(node.left)
            right = self.format_node_natural(node.right)
            op_map = {
                NodeType.AND: "AND",
                NodeType.OR: "OR",
                NodeType.XOR: "XOR",
                NodeType.IMPLIES: "IMPLIES",
                NodeType.IFF: "IF-AND-ONLY-IF"
            }
            op = op_map.get(node.node_type, "?")
            return f"({left} {op} {right})"
        return "?"

    def add_step(self, message, formal=None):
        """Add a reasoning step."""
        indent = "  " * self.depth
        self.reasoning_steps.append(f"{indent}• {message}")
        if formal:
            self.reasoning_steps.append(f"{indent}  Formal: {formal}")

    def explain_query(self, fact):
        """Generate explanation for why a fact has its truth value."""
        self.reasoning_steps = []
        self.depth = 0

        result = self._explain_fact(fact)

        summary = self._generate_summary(fact, result)

        return summary, result, self.reasoning_steps

    def _explain_fact(self, fact):
        """Explain the evaluation of a fact."""
        if fact in self.initial_facts:
            self.add_step(
                f"{fact} is TRUE (given as initial fact)",
                f"{fact} ∈ InitialFacts"
            )
            return TruthValue.TRUE

        has_rules = fact in self.engine.rules_concluding
        has_negation = f"!{fact}" in self.engine.rules_concluding

        if not has_rules and not has_negation:
            msg = (
                f"{fact} is FALSE (no rules conclude {fact}, "
                "default is false)"
            )
            self.add_step(msg, f"{fact} = ⊥")
            return TruthValue.FALSE

        can_be_true = False
        is_undetermined = False

        if has_rules:
            self.add_step(f"Checking rules that can conclude {fact}:")
            self.depth += 1

            for i, rule in enumerate(self.engine.rules_concluding[fact], 1):
                rule_str = self.format_node(rule.condition)
                conclusion_str = self.format_node(rule.conclusion)
                rule_nat = self.format_node_natural(rule.condition)
                concl_nat = (
                    self.format_node_natural(rule.conclusion))
                self.add_step(
                    f"Rule {i}: IF {rule_nat} THEN {concl_nat}",
                    f"{rule_str} ⇒ {conclusion_str}"
                )

                self.depth += 1
                condition_result = self._explain_expression(rule.condition)
                self.depth -= 1

                if condition_result == TruthValue.TRUE:
                    self.add_step(
                        f"Condition is TRUE, so {fact} is TRUE",
                        f"{rule_str} = ⊤ → {fact} = ⊤"
                    )
                    can_be_true = True
                    break
                elif condition_result == TruthValue.UNDETERMINED:
                    rule_undet = f"{rule_str} = ?"
                    self.add_step(
                        "Condition is UNDETERMINED",
                        rule_undet
                    )
                    is_undetermined = True
                else:
                    rule_false = f"{rule_str} = ⊥"
                    self.add_step(
                        "Condition is FALSE, rule does not apply",
                        rule_false
                    )

            self.depth -= 1

        if f"!{fact}" in self.engine.rules_concluding and not can_be_true:
            self.add_step(f"Checking rules that can conclude NOT {fact}:")
            self.depth += 1

            for rule in self.engine.rules_concluding[f"!{fact}"]:
                condition_result = self._explain_expression(rule.condition)
                if condition_result == TruthValue.TRUE:
                    msg = (
                        f"Contradiction: {fact} can be both "
                        "TRUE and FALSE"
                    )
                    formal = (
                        f"{fact} = ⊤ ∧ {fact} = ⊥ → "
                        f"{fact} = ?"
                    )
                    self.add_step(msg, formal)
                    if can_be_true:
                        self.depth -= 1
                        return TruthValue.UNDETERMINED

            self.depth -= 1

        if can_be_true:
            return TruthValue.TRUE
        elif is_undetermined:
            self.add_step(
                f"{fact} is UNDETERMINED (insufficient information)",
                f"{fact} = ?"
            )
            return TruthValue.UNDETERMINED
        else:
            self.add_step(
                f"{fact} is FALSE (no rule proves it true)",
                f"{fact} = ⊥"
            )
            return TruthValue.FALSE

    def _explain_expression(self, node):
        """Explain the evaluation of an expression."""
        if isinstance(node, FactNode):
            return self._explain_fact(node.fact)

        elif isinstance(node, UnaryOpNode):
            if node.node_type == NodeType.NOT:
                operand_str = self.format_node(node.operand)
                self.add_step(f"Evaluating NOT {operand_str}")
                self.depth += 1
                operand_value = self._explain_expression(node.operand)
                self.depth -= 1

                if operand_value == TruthValue.TRUE:
                    result = TruthValue.FALSE
                    self.add_step(
                        "NOT TRUE = FALSE",
                        "¬⊤ = ⊥"
                    )
                elif operand_value == TruthValue.FALSE:
                    result = TruthValue.TRUE
                    self.add_step(
                        "NOT FALSE = TRUE",
                        "¬⊥ = ⊤"
                    )
                else:
                    result = TruthValue.UNDETERMINED
                    self.add_step(
                        "NOT UNDETERMINED = UNDETERMINED",
                        "¬? = ?"
                    )
                return result

        elif isinstance(node, BinaryOpNode):
            left_str = self.format_node(node.left)
            right_str = self.format_node(node.right)

            msg = self.format_node_natural(node)
            self.add_step(
                f"Evaluating {msg}",
                self.format_node(node)
            )
            self.depth += 1

            left_value = self._explain_expression(node.left)
            right_value = self._explain_expression(node.right)

            self.depth -= 1

            if node.node_type == NodeType.AND:
                result = self.engine._eval_and(left_value, right_value)
                msg = (
                    f"{left_str}={left_value.name} AND "
                    f"{right_str}={right_value.name} = {result.name}"
                )
                formal = (
                    f"{left_str} ∧ {right_str} = "
                    f"{self._truth_symbol(result)}"
                )
                self.add_step(msg, formal)
            elif node.node_type == NodeType.OR:
                result = self.engine._eval_or(left_value, right_value)
                msg = (
                    f"{left_str}={left_value.name} OR "
                    f"{right_str}={right_value.name} = {result.name}"
                )
                formal = (
                    f"{left_str} ∨ {right_str} = "
                    f"{self._truth_symbol(result)}"
                )
                self.add_step(msg, formal)
            elif node.node_type == NodeType.XOR:
                result = self.engine._eval_xor(left_value, right_value)
                msg = (
                    f"{left_str}={left_value.name} XOR "
                    f"{right_str}={right_value.name} = {result.name}"
                )
                formal = (
                    f"{left_str} ⊕ {right_str} = "
                    f"{self._truth_symbol(result)}"
                )
                self.add_step(msg, formal)
            else:
                result = TruthValue.UNDETERMINED

            return result

        return TruthValue.UNDETERMINED

    def _truth_symbol(self, value):
        """Convert TruthValue to formal logic symbol."""
        if value == TruthValue.TRUE:
            return "⊤"
        elif value == TruthValue.FALSE:
            return "⊥"
        else:
            return "?"

    def _generate_summary(self, fact, result):
        """Generate a natural language summary."""
        if result == TruthValue.TRUE:
            summary = f"✓ {fact} is TRUE"
            if fact in self.initial_facts:
                summary += " (given as initial fact)"
            else:
                summary += " (proven by the rules)"
        elif result == TruthValue.FALSE:
            summary = f"✗ {fact} is FALSE (not proven true by any rule)"
        else:
            summary = f"? {fact} is UNDETERMINED (insufficient information)"

        return summary


def main():
    """Main entry point for reasoning visualizer."""
    if len(sys.argv) != 2:
        print("Reasoning Visualization Tool")
        print()
        print("Usage:")
        print("  python3 reasoning_visualizer.py <input_file>")
        print()
        print("This tool shows detailed reasoning for all queries.")
        return 1

    input_file = sys.argv[1]

    if not Path(input_file).exists():
        print(f"Error: Input file not found: {input_file}", file=sys.stderr)
        return 1

    try:
        with open(input_file, 'r') as f:
            content = f.read()
        rules, initial_facts, queries = parse_input_file(content)
    except Exception as e:
        print(f"Error parsing input file: {e}", file=sys.stderr)
        return 1

    visualizer = ReasoningVisualizer(rules, initial_facts)

    print("=" * 70)
    print("REASONING VISUALIZATION")
    print("=" * 70)
    facts_str = (', '.join(sorted(initial_facts))
                 if initial_facts else 'None')
    print(f"Initial facts: {facts_str}")
    print(f"Queries: {', '.join(queries)}")
    print("=" * 70)
    print()

    for query in queries:
        print(f"{'=' * 70}")
        print(f"QUERY: {query}")
        print(f"{'=' * 70}")

        summary, result, steps = visualizer.explain_query(query)

        for step in steps:
            print(step)

        print()
        print(f"CONCLUSION: {summary}")
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
