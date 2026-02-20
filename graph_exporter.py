#!/usr/bin/env python3
# *************************************************************************** #
#                                                                             #
#                                                        :::      ::::::::    #
#   graph_exporter.py                                  :+:      :+:    :+:    #
#                                                    +:+ +:+         +:+      #
#   By: iberegsz <iberegsz@student.42vienna.com>   +#+  +:+       +#+         #
#                                                +#+#+#+#+#+   +#+            #
#   Created: 2026/01/18 21:29:17 by iberegsz          #+#    #+#              #
#   Updated: 2026/01/22 04:06:32 by iberegsz         ###   ########.fr        #
#                                                                             #
# *************************************************************************** #

"""
Justification Graph Export (Bonus Feature)

Exports the reasoning/inference graph in DOT (Graphviz) and JSON formats
for visualization and analysis tools.
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from parser import (
    parse_input_file, Rule, ASTNode, NodeType,
    FactNode, UnaryOpNode, BinaryOpNode
)
from inference_engine import InferenceEngine, TruthValue


class ProvenanceNode:
    """Represents a node in the justification graph."""

    def __init__(
        self,
        fact: str,
        value: TruthValue,
        node_type: str = "derived"
    ):
        self.fact = fact
        self.value = value
        self.node_type = node_type
        self.supporting_facts: Set[str] = set()
        self.rules_used: List[str] = []

    def __repr__(self):
        return f"ProvenanceNode({self.fact}, {self.value.name})"


class JustificationGraph:
    """Builds and exports a justification graph."""

    def __init__(self, rules: List[Rule], initial_facts: Set[str]):
        self.rules = rules
        self.initial_facts = initial_facts
        self.engine = InferenceEngine(rules, initial_facts)
        self.nodes: Dict[str, ProvenanceNode] = {}
        self.edges: List[Tuple[str, str, str]] = []

    def format_node(self, node: ASTNode) -> str:
        """Format AST node as string."""
        if isinstance(node, FactNode):
            return node.fact
        elif isinstance(node, UnaryOpNode):
            if node.node_type == NodeType.NOT:
                return f"¬{self.format_node(node.operand)}"
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

    def format_rule(self, rule: Rule) -> str:
        """Format a rule for display."""
        cond = self.format_node(rule.condition)
        concl = self.format_node(rule.conclusion)
        op = "⇔" if rule.is_biconditional else "⇒"
        return f"{cond} {op} {concl}"

    def get_facts_from_node(self, node: ASTNode) -> Set[str]:
        """Extract all fact names from AST node."""
        return node.get_facts()

    def build_graph(self, queries: List[str]):
        """Build justification graph by tracing queries."""
        for fact in self.initial_facts:
            self.nodes[fact] = ProvenanceNode(
                fact, TruthValue.TRUE, "initial"
            )

        for query in queries:
            self._trace_fact(query, is_query=True)

    def _trace_fact(
        self,
        fact: str,
        is_query: bool = False,
        visited: Optional[Set[str]] = None
    ):
        """Trace evaluation of a fact and build provenance."""
        if visited is None:
            visited = set()

        if fact in visited:
            return

        visited.add(fact)

        result = self.engine.query(fact)

        if fact not in self.nodes:
            node_type = "query" if is_query else "derived"
            self.nodes[fact] = ProvenanceNode(fact, result, node_type)
        else:
            if is_query:
                self.nodes[fact].node_type = "query"

        if fact in self.initial_facts:
            return

        if fact in self.engine.rules_concluding:
            for rule in self.engine.rules_concluding[fact]:
                cond_value = self._evaluate_expression_trace(
                    rule.condition, visited
                )

                if cond_value == TruthValue.TRUE:
                    rule_str = self.format_rule(rule)
                    self.nodes[fact].rules_used.append(rule_str)

                    supporting = self.get_facts_from_node(rule.condition)
                    for support_fact in supporting:
                        self.nodes[fact].supporting_facts.add(support_fact)
                        edge = (
                            support_fact,
                            fact,
                            rule_str
                        )
                        if edge not in self.edges:
                            self.edges.append(edge)

                        self._trace_fact(support_fact, False, visited)

    def _evaluate_expression_trace(
        self,
        node: ASTNode,
        visited: Set[str]
    ) -> TruthValue:
        """Evaluate expression and trace dependencies."""
        if isinstance(node, FactNode):
            self._trace_fact(node.fact, False, visited)
            return self.engine.query(node.fact)
        elif isinstance(node, UnaryOpNode):
            if node.node_type == NodeType.NOT:
                operand_value = self._evaluate_expression_trace(
                    node.operand, visited
                )
                if operand_value == TruthValue.TRUE:
                    return TruthValue.FALSE
                elif operand_value == TruthValue.FALSE:
                    return TruthValue.TRUE
                else:
                    return TruthValue.UNDETERMINED
        elif isinstance(node, BinaryOpNode):
            left_value = self._evaluate_expression_trace(
                node.left, visited
            )
            right_value = self._evaluate_expression_trace(
                node.right, visited
            )

            if node.node_type == NodeType.AND:
                return self.engine._eval_and(left_value, right_value)
            elif node.node_type == NodeType.OR:
                return self.engine._eval_or(left_value, right_value)
            elif node.node_type == NodeType.XOR:
                return self.engine._eval_xor(left_value, right_value)

        return TruthValue.UNDETERMINED

    def export_dot(self, output_file: str):
        """Export graph in DOT format for Graphviz."""
        lines = ["digraph JustificationGraph {"]
        lines.append("  rankdir=BT;")
        lines.append("  node [shape=box, style=rounded];")
        lines.append("")

        for fact, node in self.nodes.items():
            if node.node_type == "initial":
                color = "lightblue"
                shape = "box"
            elif node.node_type == "query":
                color = "lightgreen" if node.value == TruthValue.TRUE else (
                    "lightcoral" if node.value == TruthValue.FALSE
                    else "lightyellow"
                )
                shape = "doubleoctagon"
            else:
                color = "white"
                shape = "box"

            label = f"{fact}\\n{node.value.name}"
            lines.append(
                f'  "{fact}" [label="{label}", '
                f'fillcolor={color}, style=filled, shape={shape}];'
            )

        lines.append("")

        for source, target, rule in self.edges:
            rule_label = rule.replace('"', '\\"')
            lines.append(
                f'  "{source}" -> "{target}" '
                f'[label="{rule_label}"];'
            )

        lines.append("}")

        with open(output_file, 'w') as f:
            f.write('\n'.join(lines))

    def export_json(self, output_file: str):
        """Export graph in JSON format."""
        graph_data = {
            "nodes": [],
            "edges": [],
            "metadata": {
                "total_rules": len(self.rules),
                "initial_facts": sorted(self.initial_facts),
                "total_nodes": len(self.nodes)
            }
        }

        for fact, node in self.nodes.items():
            node_data = {
                "id": fact,
                "value": node.value.name,
                "type": node.node_type,
                "supporting_facts": sorted(node.supporting_facts),
                "rules_used": node.rules_used
            }
            graph_data["nodes"].append(node_data)

        for source, target, rule in self.edges:
            edge_data = {
                "from": source,
                "to": target,
                "rule": rule
            }
            graph_data["edges"].append(edge_data)

        with open(output_file, 'w') as f:
            json.dump(graph_data, f, indent=2)


def main():
    """Main entry point for graph exporter."""
    if len(sys.argv) < 2:
        print("Justification Graph Export Tool")
        print()
        print("Usage:")
        print("  python3 graph_exporter.py <input_file> [options]")
        print()
        print("Options:")
        print("  --dot <file>   Export to DOT format (Graphviz)")
        print("  --json <file>  Export to JSON format")
        print()
        print("Examples:")
        print("  python3 graph_exporter.py test.txt --dot graph.dot")
        print("  python3 graph_exporter.py test.txt --json graph.json")
        print(
            "  python3 graph_exporter.py test.txt "
            "--dot graph.dot --json graph.json"
        )
        return 1

    input_file = sys.argv[1]

    if not Path(input_file).exists():
        print(f"Error: Input file not found: {input_file}", file=sys.stderr)
        return 1

    dot_output = None
    json_output = None

    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--dot" and i + 1 < len(sys.argv):
            dot_output = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--json" and i + 1 < len(sys.argv):
            json_output = sys.argv[i + 1]
            i += 2
        else:
            print(f"Unknown option: {sys.argv[i]}", file=sys.stderr)
            return 1

    if not dot_output and not json_output:
        print("Error: Specify at least one output format", file=sys.stderr)
        print("Use --dot <file> and/or --json <file>", file=sys.stderr)
        return 1

    try:
        with open(input_file, 'r') as f:
            content = f.read()
        rules, initial_facts, queries = parse_input_file(content)
    except Exception as e:
        print(f"Error parsing input file: {e}", file=sys.stderr)
        return 1

    print("Building justification graph...")
    graph = JustificationGraph(rules, initial_facts)
    graph.build_graph(queries)

    print(f"Graph contains {len(graph.nodes)} nodes and "
          f"{len(graph.edges)} edges")

    if dot_output:
        graph.export_dot(dot_output)
        print(f"DOT export written to: {dot_output}")
        print(
            "  Visualize with: dot -Tpng "
            f"{dot_output} -o graph.png"
        )

    if json_output:
        graph.export_json(json_output)
        print(f"JSON export written to: {json_output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
