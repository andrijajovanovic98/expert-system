#!/usr/bin/env python3
# *************************************************************************** #
#                                                                             #
#                                                        :::      ::::::::    #
#   interactive_mode.py                                :+:      :+:    :+:    #
#                                                    +:+ +:+         +:+      #
#   By: iberegsz <iberegsz@student.42vienna.com>   +#+  +:+       +#+         #
#                                                +#+#+#+#+#+   +#+            #
#   Created: 2026/01/18 21:18:23 by iberegsz          #+#    #+#              #
#   Updated: 2026/01/22 04:07:26 by iberegsz         ###   ########.fr        #
#                                                                             #
# *************************************************************************** #

"""
Interactive Fact Validation Mode (Bonus Feature #1)

Allows users to change facts interactively to check the same query
against different inputs without modifying the source file.
"""

import sys
from pathlib import Path
from parser import parse_input_file
from inference_engine import InferenceEngine, TruthValue
from graph_exporter import JustificationGraph

try:
    import readline
    import atexit

    _SCRIPT_DIR = Path(__file__).resolve().parent
    _HISTFILE = _SCRIPT_DIR / '.expert_system_history'

    try:
        readline.read_history_file(str(_HISTFILE))
    except Exception:
        pass

    atexit.register(lambda: readline.write_history_file(str(_HISTFILE)))
    readline.set_history_length(1000)
except Exception:
    pass


def print_separator():
    """Print a separator line."""
    print("=" * 70)


def print_facts_status(facts_set):
    """Print current facts in a nice format."""
    if not facts_set:
        print("Currently TRUE facts: (none)")
    else:
        print(f"Currently TRUE facts: {', '.join(sorted(facts_set))}")


def print_query_result(fact, value):
    """Print a single query result."""
    if value == TruthValue.TRUE:
        symbol = "✓"
        color = "\033[92m"
    elif value == TruthValue.FALSE:
        symbol = "✗"
        color = "\033[91m"
    else:
        symbol = "?"
        color = "\033[93m"

    reset = "\033[0m"
    print(f"{color}{fact}: {symbol} {value.name}{reset}")


def print_help():
    """Print help information for interactive mode."""
    print("\nInteractive Mode Commands:")
    print("  +A, +B, ...  - Set fact(s) to TRUE (persist)")
    print("  -A, -B, ...  - Remove fact(s) from current facts (persist)")
    print("  ?A, ?B, ...  - Query fact(s) using current facts + what-if stack")
    print("  facts        - Show current facts")
    print("  reset        - Reset to original initial facts")
    print("  rules        - Show loaded rules")
    print("  push +A      - Push a temporary assertion (what-if)")
    print("  pop          - Pop last temporary assertion")
    print("  temp         - Show temporary assertions stack")
    print("  clear_temp   - Clear temporary assertions")
    print("  suggest A    - Try single-fact additions to make A TRUE")
    print("  export dot <f>  - Export justification graph as DOT file")
    print("  export json <f> - Export justification graph as JSON file")
    print("  help         - Show this help")
    print("  quit, exit   - Exit interactive mode")
    print()


def format_rule(rule):
    """Format a rule for display."""
    from parser import NodeType, FactNode, UnaryOpNode, BinaryOpNode

    def format_node(node):
        if isinstance(node, FactNode):
            return node.fact
        elif isinstance(node, UnaryOpNode):
            if node.node_type == NodeType.NOT:
                return f"!{format_node(node.operand)}"
        elif isinstance(node, BinaryOpNode):
            left = format_node(node.left)
            right = format_node(node.right)
            op = {
                NodeType.AND: " + ",
                NodeType.OR: " | ",
                NodeType.XOR: " ^ ",
                NodeType.IMPLIES: " => ",
                NodeType.IFF: " <=> "
            }.get(node.node_type, " ? ")
            return f"({left}{op}{right})"
        return "?"

    op = "<=>" if rule.is_biconditional else "=>"
    return f"{format_node(rule.condition)} {op} {format_node(rule.conclusion)}"


def run_interactive_mode(input_file):
    """Run the interactive fact validation mode."""
    if not Path(input_file).exists():
        print(f"Error: Input file not found: {input_file}", file=sys.stderr)
        return 1

    try:
        with open(input_file, 'r') as f:
            content = f.read()
        rules, initial_facts, original_queries = parse_input_file(content)
    except Exception as e:
        print(f"Error parsing input file: {e}", file=sys.stderr)
        return 1

    original_facts = set(initial_facts)
    current_facts = set(initial_facts)
    temp_stack = []

    all_facts = set()
    for rule in rules:
        all_facts.update(rule.get_all_facts())
    all_facts.update(initial_facts)

    print_separator()
    print("INTERACTIVE FACT VALIDATION MODE")
    print_separator()
    print(f"Loaded {len(rules)} rule(s) from {input_file}")
    print_facts_status(current_facts)
    print_help()

    while True:
        try:
            user_input = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting interactive mode.")
            break

        if not user_input:
            continue

        cmd = user_input.lower()

        if cmd in ['quit', 'exit', 'q']:
            print("Exiting interactive mode.")
            break

        elif cmd == 'help':
            print_help()

        elif cmd == 'facts':
            print_facts_status(current_facts)

        elif cmd == 'reset':
            current_facts = set(original_facts)
            temp_stack.clear()
            print("Reset to original facts.")
            print_facts_status(current_facts)

        elif cmd == 'rules':
            print(f"\nLoaded {len(rules)} rule(s):")
            for i, rule in enumerate(rules, 1):
                print(f"  {i}. {format_rule(rule)}")

        elif user_input.startswith('+'):
            facts_to_add = user_input[1:].upper().replace(
                ',', '').replace(' ', '')
            added = []
            for fact in facts_to_add:
                if fact.isalpha() and len(fact) == 1:
                    current_facts.add(fact)
                    added.append(fact)
                else:
                    print(f"Invalid fact: {fact}")
            if added:
                print(f"Added fact(s): {', '.join(added)}")
                print_facts_status(current_facts)

        elif user_input.startswith('-'):
            facts_to_remove = user_input[1:].upper().replace(
                ',', '').replace(' ', '')
            removed = []
            for fact in facts_to_remove:
                if fact.isalpha() and len(fact) == 1:
                    current_facts.discard(fact)
                    removed.append(fact)
                else:
                    print(f"Invalid fact: {fact}")
            if removed:
                print(f"Removed fact(s): {', '.join(removed)}")
                print_facts_status(current_facts)

        elif cmd.startswith('push'):
            rest = user_input[4:].strip()
            if not rest:
                print("Usage: push +A or push -A (use + to add, - to remove)")
                continue
            adds = set()
            removes = set()
            if rest.startswith('+'):
                for f in rest[1:].upper():
                    if f.isalpha():
                        adds.add(f)
            elif rest.startswith('-'):
                for f in rest[1:].upper():
                    if f.isalpha():
                        removes.add(f)
            else:
                print("Push must start with + or -")
                continue

            temp_stack.append({'add': adds, 'remove': removes})
            print(f"Pushed temporary assertion: +{''.join(sorted(adds))} \
                  - {''.join(sorted(removes))}")

        elif cmd == 'pop':
            if not temp_stack:
                print('No temporary assertions to pop.')
            else:
                item = temp_stack.pop()
                print(f"Popped: +{''.join(sorted(item['add']))} \
                      - {''.join(sorted(item['remove']))}")

        elif cmd == 'temp':
            if not temp_stack:
                print('Temporary stack is empty.')
            else:
                print('Temporary assertions (last is top):')
                for i, item in enumerate(temp_stack, 1):
                    print(f"  {i}. +{''.join(sorted(item['add']))} \
                          - {''.join(sorted(item['remove']))}")

        elif cmd == 'clear_temp':
            temp_stack.clear()
            print('Cleared temporary assertions.')

        elif cmd.startswith('suggest'):
            parts = user_input.split()
            if len(parts) != 2:
                print('Usage: suggest A')
                continue
            target = parts[1].upper()
            if not (len(target) == 1 and target.isalpha()):
                print('Suggestion target must be a single fact letter.')
                continue

            def compute_effective_facts():
                eff = set(current_facts)
                for item in temp_stack:
                    eff.update(item['add'])
                    for r in item['remove']:
                        eff.discard(r)
                return eff

            suggestions = []
            base_eff = compute_effective_facts()
            engine_base = InferenceEngine(rules, base_eff)
            base_result = engine_base.query(target)
            if base_result == TruthValue.TRUE:
                print(f"{target} is already TRUE with current facts.")
                continue

            for cand in sorted(all_facts):
                if cand == target:
                    continue
                if cand in base_eff:
                    continue
                eff = set(base_eff)
                eff.add(cand)
                engine = InferenceEngine(rules, eff)
                res = engine.query(target)
                if res == TruthValue.TRUE:
                    suggestions.append(cand)

            if suggestions:
                print(f"Asserting any of these would make {target} \
                    TRUE: {', '.join(suggestions)}")
            else:
                print(f"No single-fact suggestion found to make {target} \
                    TRUE.")

        elif cmd.startswith('export'):
            parts = user_input.split()
            if len(parts) < 3:
                print('Usage: export dot <filename> or export json <filename>')
                continue

            export_format = parts[1].lower()
            filename = parts[2]

            if export_format not in ['dot', 'json']:
                print('Format must be "dot" or "json"')
                continue

            def compute_effective_facts():
                eff = set(current_facts)
                for item in temp_stack:
                    eff.update(item['add'])
                    for r in item['remove']:
                        eff.discard(r)
                return eff

            try:
                eff = compute_effective_facts()
                graph = JustificationGraph(rules, eff)

                query_list = sorted(
                    [f for f in all_facts if not f.startswith('!')])
                graph.build_graph(query_list)

                if export_format == 'dot':
                    graph.export_dot(filename)
                    print(f'Graph exported to {filename} (DOT format)')
                    print(
                        f'  Visualize with: dot -Tpng {filename} -o graph.png')
                else:
                    graph.export_json(filename)
                    print(f'Graph exported to {filename} (JSON format)')
            except Exception as e:
                print(f'Export failed: {e}')

        elif user_input.startswith('?'):
            queries = user_input[1:].upper().replace(',', '').replace(' ', '')
            if not queries:
                print("No queries specified.")
                continue

            engine = InferenceEngine(rules, current_facts)

            print_separator()
            print("QUERY RESULTS")
            print_separator()

            for fact in queries:
                if fact.isalpha() and len(fact) == 1:
                    result = engine.query(fact)
                    print_query_result(fact, result)
                else:
                    print(f"Invalid query: {fact}")

        else:
            print(f"Unknown command: {user_input}")
            print("Type 'help' for available commands.")

    return 0


def main():
    """Main entry point for interactive mode."""
    if len(sys.argv) != 2:
        print("Interactive Fact Validation Mode")
        print()
        print("Usage:")
        print("  python3 interactive_mode.py <input_file>")
        print()
        print("This mode allows you to change facts interactively and")
        print("re-query without modifying the source file.")
        return 1

    return run_interactive_mode(sys.argv[1])


if __name__ == "__main__":
    sys.exit(main())
