#!/usr/bin/env python3
# *************************************************************************** #
#                                                                             #
#                                                        :::      ::::::::    #
#   knowledge_graph.py                                 :+:      :+:    :+:    #
#                                                    +:+ +:+         +:+      #
#   By: iberegsz <iberegsz@student.42vienna.com>   +#+  +:+       +#+         #
#                                                +#+#+#+#+#+   +#+            #
#   Created: 2026/01/18 21:39:51 by iberegsz          #+#    #+#              #
#   Updated: 2026/01/23 05:46:26 by iberegsz         ###   ########.fr        #
#                                                                             #
# *************************************************************************** #

"""
Demonstration of Level-5 Knowledge Graph capabilities.

This script shows the advanced features of the global knowledge graph:
- O(1) lookup of rules concluding/using facts
- Graph traversal for dependency analysis
- Bidirectional edge navigation
"""

import sys
from pathlib import Path
from parser import parse_input_file
from knowledge_graph import KnowledgeGraph


def demonstrate_graph(content: str | None = None):
    """Demonstrate knowledge graph features.

    If `content` is None, a built-in demo scenario is used. Otherwise the
    provided text is parsed as the input file contents.
    """

    if content is None:
        content = """
A + B => C
C => D
D => E
B => F
A <=> G
=A
?CDEFG
"""

    rules, initial_facts, queries = parse_input_file(content)
    graph = KnowledgeGraph(rules, initial_facts)

    print("=" * 70)
    print("KNOWLEDGE GRAPH DEMONSTRATION")
    print("=" * 70)
    print()

    print(f"Graph: {graph}")
    print(f"Total facts: {len(graph.fact_nodes)}")
    print(f"Total rule nodes: {len(graph.rule_nodes)}")
    print()

    print("FACT NODES:")
    print("-" * 70)
    for fact_name in sorted(graph.fact_nodes.keys()):
        fact_node = graph.fact_nodes[fact_name]
        initial_mark = " (INITIAL)" if fact_node.is_initial else ""
        print(f"  {fact_name}{initial_mark}")
        print(f"    -> Concluded by: {len(fact_node.concluding_rules)} rule(s)"
              )
        print(f"    -> Used by: {len(fact_node.used_by_rules)} rule(s)")
    print()

    print("RULE NODES:")
    print("-" * 70)
    for rule_node in graph.rule_nodes:
        cond_facts = [f.fact for f in rule_node.condition_facts]
        concl_facts = [f.fact for f in rule_node.conclusion_facts]
        print(f"  R{rule_node.rule_id}: {cond_facts} => {concl_facts}")
    print()

    print("O(1) LOOKUP EXAMPLES:")
    print("-" * 70)

    fact = "C"
    rules = graph.get_rules_concluding(fact)
    print(f"Rules concluding '{fact}': {len(rules)} rule(s)")
    for rule_node in rules:
        print(f"  - R{rule_node.rule_id}")

    rules_using = graph.get_rules_using(fact)
    print(f"Rules using '{fact}' in condition: {len(rules_using)} rule(s)")
    for rule_node in rules_using:
        print(f"  - R{rule_node.rule_id}")
    print()

    print("DEPENDENCY CHAIN ANALYSIS:")
    print("-" * 70)
    for query_fact in ['E', 'F', 'G']:
        deps = graph.get_dependency_chain(query_fact)
        print(f"{query_fact} depends on: ")
        print(f"{sorted(deps) if deps else 'nothing (initial or no rules)'}")
    print()

    print("BIDIRECTIONAL EDGE NAVIGATION:")
    print("-" * 70)
    fact_node = graph.get_fact_node('D')
    if fact_node:
        print("Starting from fact 'D':")
        print("  <- Rules that conclude D:")
        for rule_node in fact_node.concluding_rules:
            cond = [f.fact for f in rule_node.condition_facts]
            print(f"      R{rule_node.rule_id}: {cond} => D")

        print("  -> Rules that use D:")
        for rule_node in fact_node.used_by_rules:
            concl = [f.fact for f in rule_node.conclusion_facts]
            print(f"      R{rule_node.rule_id}: D => {concl}")
    print()

    print("=" * 70)
    print("BENEFITS OF GRAPH DATA STRUCTURE:")
    print("=" * 70)
    print("- O(1) lookup for rules concluding a fact")
    print("- O(1) lookup for rules using a fact")
    print("- Bidirectional edge navigation")
    print("- Transitive dependency analysis")
    print("- Explicit node objects with metadata")
    print("- Easy graph visualization export")
    print("- Support for cycle detection")
    print("- Foundation for proof tracing")
    print()


def _read_file(path: str) -> str:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    if not p.is_file():
        raise IsADirectoryError(f"Not a file: {path}")
    return p.read_text()


def main(argv: list | None = None) -> int:
    """CLI entrypoint for the demo.

    Returns exit code (0 success, non-zero failure).
    """
    argv = list(argv) if argv is not None else sys.argv[1:]

    try:
        if len(argv) == 0:
            demonstrate_graph()
            return 0

        if len(argv) == 1:
            input_path = argv[0]
            content = _read_file(input_path)
            demonstrate_graph(content)
            return 0

        print("Usage: python3 demo_graph.py [input_file]", file=sys.stderr)
        return 2
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 3
    except IsADirectoryError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 4
    except Exception as e:
        print(f"Unhandled error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
