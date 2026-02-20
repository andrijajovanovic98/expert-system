#!/usr/bin/env python3
# *************************************************************************** #
#                                                                             #
#                                                        :::      ::::::::    #
#   debug.py                                           :+:      :+:    :+:    #
#                                                    +:+ +:+         +:+      #
#   By: iberegsz <iberegsz@student.42vienna.com>   +#+  +:+       +#+         #
#                                                +#+#+#+#+#+   +#+            #
#   Created: 2025/10/22 11:22:18 by iberegsz          #+#    #+#              #
#   Updated: 2026/01/19 19:16:31 by iberegsz         ###   ########.fr        #
#                                                                             #
# *************************************************************************** #

"""
Debug version with tracing
"""

import sys

from parser import parse_input_file
from inference_engine import InferenceEngine


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 debug.py <input_file>")
        return 1

    input_file = sys.argv[1]

    with open(input_file, 'r') as f:
        content = f.read()

    rules, initial_facts, queries = parse_input_file(content)

    print(f"Parsed {len(rules)} rules:")
    for i, rule in enumerate(rules, 1):
        print(f"  {i}. {rule}")

    print(f"\nInitial facts: {initial_facts}")
    print(f"Queries: {queries}")

    engine = InferenceEngine(rules, initial_facts)

    print("\nRules index:")
    for fact, rule_list in engine.rules_concluding.items():
        print(f"  {fact} can be concluded by {len(rule_list)} rule(s):")
        for rule in rule_list:
            print(f"    - {rule}")

    print("\nProcessing queries:")
    for query in queries:
        result = engine.query(query)
        print(f"  {query} = {result}")


if __name__ == "__main__":
    sys.exit(main())
