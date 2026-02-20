#!/usr/bin/env python3
# *************************************************************************** #
#                                                                             #
#                                                        :::      ::::::::    #
#   statistics_analyzer.py                             :+:      :+:    :+:    #
#                                                    +:+ +:+         +:+      #
#   By: iberegsz <iberegsz@student.42vienna.com>   +#+  +:+       +#+         #
#                                                +#+#+#+#+#+   +#+            #
#   Created: 2026/01/18 21:18:13 by iberegsz          #+#    #+#              #
#   Updated: 2026/01/19 19:33:41 by iberegsz         ###   ########.fr        #
#                                                                             #
# *************************************************************************** #

"""
Statistics and Metrics Analyzer (Creative Bonus Feature)

Provides comprehensive statistics about the rule set, including:
- Rule complexity metrics
- Fact dependencies
- Inference depth
- Performance analysis
"""

import sys
from pathlib import Path
from collections import defaultdict
from parser import (
    parse_input_file, NodeType, FactNode,
    UnaryOpNode, BinaryOpNode
)
from inference_engine import InferenceEngine


class StatisticsAnalyzer:
    """Analyzes rules and provides statistics."""

    def __init__(self, rules, initial_facts):
        self.rules = rules
        self.initial_facts = initial_facts
        self.engine = InferenceEngine(rules, initial_facts)

    def count_operators(self, node):
        """Count operators in an AST node."""
        counts = defaultdict(int)

        if isinstance(node, FactNode):
            pass
        elif isinstance(node, UnaryOpNode):
            counts[node.node_type] += 1
            sub_counts = self.count_operators(node.operand)
            for k, v in sub_counts.items():
                counts[k] += v
        elif isinstance(node, BinaryOpNode):
            counts[node.node_type] += 1
            left_counts = self.count_operators(node.left)
            right_counts = self.count_operators(node.right)
            for k, v in left_counts.items():
                counts[k] += v
            for k, v in right_counts.items():
                counts[k] += v

        return counts

    def get_rule_complexity(self, rule):
        """Calculate complexity score for a rule."""
        cond_ops = self.count_operators(rule.condition)
        concl_ops = self.count_operators(rule.conclusion)

        total = sum(cond_ops.values()) + sum(concl_ops.values())
        return total

    def get_rule_depth(self, node, depth=0):
        """Get maximum depth of an AST."""
        if isinstance(node, FactNode):
            return depth
        elif isinstance(node, UnaryOpNode):
            return self.get_rule_depth(node.operand, depth + 1)
        elif isinstance(node, BinaryOpNode):
            left_depth = self.get_rule_depth(node.left, depth + 1)
            right_depth = self.get_rule_depth(node.right, depth + 1)
            return max(left_depth, right_depth)
        return depth

    def analyze_rules(self):
        """Analyze all rules and return statistics."""
        stats = {
            'total_rules': len(self.rules),
            'biconditional_rules': 0,
            'total_operators': defaultdict(int),
            'complexity_scores': [],
            'max_depth': 0,
            'facts_used': set(),
            'facts_concluded': set(),
            'rule_types': defaultdict(int),
        }

        for rule in self.rules:
            if rule.is_biconditional:
                stats['biconditional_rules'] += 1

            cond_ops = self.count_operators(rule.condition)
            concl_ops = self.count_operators(rule.conclusion)

            for k, v in cond_ops.items():
                stats['total_operators'][k] += v
            for k, v in concl_ops.items():
                stats['total_operators'][k] += v

            complexity = self.get_rule_complexity(rule)
            stats['complexity_scores'].append(complexity)

            cond_depth = self.get_rule_depth(rule.condition)
            concl_depth = self.get_rule_depth(rule.conclusion)
            max_rule_depth = max(cond_depth, concl_depth)
            stats['max_depth'] = max(stats['max_depth'], max_rule_depth)

            stats['facts_used'].update(rule.condition.get_facts())
            stats['facts_concluded'].update(rule.conclusion.get_facts())

        if stats['complexity_scores']:
            total_complexity = sum(stats['complexity_scores'])
            count = len(stats['complexity_scores'])
            stats['avg_complexity'] = total_complexity / count
            stats['max_complexity'] = max(stats['complexity_scores'])
            stats['min_complexity'] = min(stats['complexity_scores'])

        stats['facts_used'] = sorted(stats['facts_used'])
        stats['facts_concluded'] = sorted(
            stats['facts_concluded'])

        return stats

    def analyze_dependencies(self):
        """Analyze fact dependencies."""
        dependencies = defaultdict(set)

        for fact in self.engine.all_facts:
            if fact.startswith('!'):
                continue

            if fact in self.engine.rules_concluding:
                for rule in self.engine.rules_concluding[fact]:
                    deps = rule.condition.get_facts()
                    dependencies[fact].update(deps)

        return dependencies

    def print_statistics(self):
        """Print comprehensive statistics."""
        stats = self.analyze_rules()
        deps = self.analyze_dependencies()

        print("=" * 70)
        print("RULE SET STATISTICS")
        print("=" * 70)
        print()

        print("BASIC METRICS")
        print("-" * 70)
        print(f"Total rules:            {stats['total_rules']}")
        print(f"Biconditional rules:    {stats['biconditional_rules']}")
        regular = stats['total_rules'] - stats['biconditional_rules']
        print(f"Regular rules:          {regular}")
        print()

        print("FACTS")
        print("-" * 70)
        init_facts_str = (', '.join(sorted(self.initial_facts))
                          if self.initial_facts else 'None')
        print(f"Initial facts:          {init_facts_str}")
        used_str = ', '.join(stats['facts_used'])
        print(
            f"Total facts used:       {len(stats['facts_used'])} "
            f"({used_str})")
        concl_str = ', '.join(stats['facts_concluded'])
        print(
            f"Facts concluded:        {len(stats['facts_concluded'])} "
            f"({concl_str})")
        print()

        print("OPERATORS USED")
        print("-" * 70)
        op_names = {
            NodeType.NOT: "NOT (!)",
            NodeType.AND: "AND (+)",
            NodeType.OR: "OR (|)",
            NodeType.XOR: "XOR (^)",
            NodeType.IMPLIES: "IMPLIES (=>)",
            NodeType.IFF: "IFF (<=>)",
        }
        sorted_ops = sorted(
            stats['total_operators'].items(), key=lambda x: -x[1])
        for op_type, count in sorted_ops:
            op_name = op_names.get(op_type, str(op_type))
            print(f"  {op_name:20} {count:3} times")
        print()

        if stats['complexity_scores']:
            print("COMPLEXITY METRICS")
            print("-" * 70)
            print(f"Average complexity:     {stats['avg_complexity']:.2f}")
            print(f"Maximum complexity:     {stats['max_complexity']}")
            print(f"Minimum complexity:     {stats['min_complexity']}")
            print(f"Maximum nesting depth:  {stats['max_depth']}")
            print()

        if deps:
            print("FACT DEPENDENCIES")
            print("-" * 70)
            for fact, dependencies in sorted(deps.items()):
                if dependencies:
                    dep_str = ', '.join(sorted(dependencies))
                    print(f"  {fact} depends on: {dep_str}")
            print()

        if stats['complexity_scores']:
            print("MOST COMPLEX RULES")
            print("-" * 70)
            rules_with_complexity = list(
                zip(self.rules, stats['complexity_scores']))
            rules_with_complexity.sort(key=lambda x: -x[1])

            top_rules = rules_with_complexity[:5]
            for i, (rule, complexity) in enumerate(top_rules, 1):
                rule_str = self.format_rule(rule)
                print(f"  {i}. [{complexity}] {rule_str}")
            print()

    def format_rule(self, rule):
        """Format a rule for display."""
        def format_node(node):
            if isinstance(node, FactNode):
                return node.fact
            elif isinstance(node, UnaryOpNode):
                if node.node_type == NodeType.NOT:
                    return f"!{format_node(node.operand)}"
            elif isinstance(node, BinaryOpNode):
                left = format_node(node.left)
                right = format_node(node.right)
                op_map = {
                    NodeType.AND: " + ",
                    NodeType.OR: " | ",
                    NodeType.XOR: " ^ ",
                    NodeType.IMPLIES: " => ",
                    NodeType.IFF: " <=> "
                }
                op = op_map.get(node.node_type, " ? ")
                if isinstance(node.left, BinaryOpNode):
                    left = f"({left})"
                if isinstance(node.right, BinaryOpNode):
                    right = f"({right})"
                return f"{left}{op}{right}"
            return "?"

        op = "<=>" if rule.is_biconditional else "=>"
        cond_str = format_node(rule.condition)
        concl_str = format_node(rule.conclusion)
        return f"{cond_str} {op} {concl_str}"


def main():
    """Main entry point for statistics analyzer."""
    if len(sys.argv) != 2:
        print("Statistics and Metrics Analyzer")
        print()
        print("Usage:")
        msg = "  python3 statistics_analyzer.py <input_file>"
        print(msg)
        print()
        msg2 = (
            "Provides comprehensive statistics "
            "about the rule set."
        )
        print(msg2)
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

    analyzer = StatisticsAnalyzer(rules, initial_facts)

    analyzer.print_statistics()

    return 0


if __name__ == "__main__":
    sys.exit(main())
