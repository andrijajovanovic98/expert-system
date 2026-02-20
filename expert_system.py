#!/usr/bin/env python3
# *************************************************************************** #
#                                                                             #
#                                                        :::      ::::::::    #
#   expert_system.py                                   :+:      :+:    :+:    #
#                                                    +:+ +:+         +:+      #
#   By: iberegsz <iberegsz@student.42vienna.com>   +#+  +:+       +#+         #
#                                                +#+#+#+#+#+   +#+            #
#   Created: 2025/10/22 11:10:06 by iberegsz          #+#    #+#              #
#   Updated: 2026/01/19 19:16:14 by iberegsz         ###   ########.fr        #
#                                                                             #
# *************************************************************************** #

"""
Expert System - Propositional Calculus Inference Engine
Main entry point for the expert system.

Usage: python3 expert_system.py <input_file>
"""

import sys
from pathlib import Path

from parser import parse_input_file
from inference_engine import InferenceEngine, TruthValue


def print_error(message: str):
    """Print error message to stderr."""
    print(f"Error: {message}", file=sys.stderr)


def print_rule_summary(rules, initial_facts):
    """Print a summary of loaded rules and facts."""
    print("=" * 60)
    print("EXPERT SYSTEM - PROPOSITIONAL CALCULUS")
    print("=" * 60)
    print(f"\nLoaded {len(rules)} rule(s)")
    initial_str = (
        ", ".join(sorted(initial_facts)) if initial_facts else "None"
    )
    print(f"Initial facts: {initial_str}")
    print()


def print_query_results(results: dict, verbose: bool = True):
    """Print query results in a clear format."""
    print("=" * 60)
    print("QUERY RESULTS")
    print("=" * 60)

    for fact, value in results.items():
        if value == TruthValue.TRUE:
            symbol = "✓"
        elif value == TruthValue.FALSE:
            symbol = "✗"
        else:
            symbol = "?"

        status = value.name
        print(f"{fact}: {symbol} {status}")

    print()


def validate_input(rules, initial_facts, queries):
    """
    Validate the input for errors and contradictions.
    Returns: (is_valid, error_message)
    """
    if not queries:
        return False, "No queries specified. Use ?<FACTS> to specify queries."

    all_facts = set(initial_facts)
    for rule in rules:
        all_facts.update(rule.get_all_facts())

    for fact in all_facts:
        if fact.startswith('!'):
            fact = fact[1:]
        if not (len(fact) == 1 and fact.isupper()):
            msg = (
                f"Invalid fact name: {fact}. "
                "Facts must be single uppercase letters (A-Z)."
            )
            return False, msg

    for letter_code in range(ord('A'), ord('Z') + 1):
        letter = chr(letter_code)
        if letter in all_facts and ('!' + letter) in all_facts:
            return False, f"Contradiction: {letter} "
            "is both asserted and negated."

    for q in queries:
        qfact = q[1:] if q.startswith('!') else q
        if not (len(qfact) == 1 and qfact.isupper()):
            return False, f"Invalid query: {q}. "
            "Queries must be single uppercase letters (A-Z)."
        pass

    return True, ""


def run_expert_system(input_file: str, verbose: bool = True):
    """
    Main function to run the expert system.

    Args:
        input_file: Path to the input file
        verbose: Whether to print detailed output

    Returns:
        0 on success, 1 on error
    """
    if not Path(input_file).exists():
        print_error(f"Input file not found: {input_file}")
        return 1

    try:
        with open(input_file, 'r') as f:
            content = f.read()
    except Exception as e:
        print_error(f"Failed to read input file: {e}")
        return 1

    try:
        rules, initial_facts, queries = parse_input_file(content)
    except SyntaxError as e:
        print_error(f"Syntax error in input file: {e}")
        return 1
    except Exception as e:
        print_error(f"Failed to parse input file: {e}")
        return 1

    is_valid, error_message = validate_input(rules, initial_facts, queries)
    if not is_valid:
        print_error(error_message)
        return 1

    if verbose:
        print_rule_summary(rules, initial_facts)

    try:
        engine = InferenceEngine(rules, initial_facts)
    except Exception as e:
        print_error(f"Failed to initialize inference engine: {e}")
        return 1

    try:
        results = engine.query_all(queries)
    except Exception as e:
        print_error(f"Error during inference: {e}")
        return 1

    print_query_results(results, verbose)

    return 0


def print_usage():
    """Print usage information."""
    print("Expert System - Propositional Calculus Inference Engine")
    print()
    print("Usage:")
    print("  python3 expert_system.py <input_file>")
    print()
    print("Input file format:")
    print("  - Rules: A + B => C  (if A and B then C)")
    print("  - Initial facts: =ABC  (A, B, and C are true)")
    print("  - Queries: ?XYZ  (query X, Y, and Z)")
    print()
    print("Operators:")
    print("  !  : NOT")
    print("  +  : AND")
    print("  |  : OR")
    print("  ^  : XOR (exclusive OR)")
    print("  => : IMPLIES")
    print("  <=>: IF AND ONLY IF (biconditional)")
    print("  () : Parentheses for grouping")
    print()
    print("Comments start with # and continue to end of line.")
    print()


def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print_usage()
        return 1

    input_file = sys.argv[1]

    if input_file in ['-h', '--help', 'help']:
        print_usage()
        return 0

    return run_expert_system(input_file, verbose=True)


if __name__ == "__main__":
    sys.exit(main())
