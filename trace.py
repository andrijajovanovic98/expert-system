#!/usr/bin/env python3
# *************************************************************************** #
#                                                                             #
#                                                        :::      ::::::::    #
#   trace.py                                           :+:      :+:    :+:    #
#                                                    +:+ +:+         +:+      #
#   By: iberegsz <iberegsz@student.42vienna.com>   +#+  +:+       +#+         #
#                                                +#+#+#+#+#+   +#+            #
#   Created: 2025/10/22 11:21:39 by iberegsz          #+#    #+#              #
#   Updated: 2026/01/19 19:31:53 by iberegsz         ###   ########.fr        #
#                                                                             #
# *************************************************************************** #

"""
Debug with detailed tracing
"""

import sys
from parser import parse_input_file
from inference_engine import InferenceEngine

original_evaluate_fact = InferenceEngine._evaluate_fact


def traced_evaluate_fact(self, fact):
    indent = "  " * len(self.evaluating)
    print(f"{indent}Evaluating {fact}...")
    result = original_evaluate_fact(self, fact)
    print(f"{indent}  -> {result}")
    return result


InferenceEngine._evaluate_fact = traced_evaluate_fact


def main():
    input_file = sys.argv[1]

    with open(input_file, 'r') as f:
        content = f.read()

    rules, initial_facts, queries = parse_input_file(content)
    engine = InferenceEngine(rules, initial_facts)

    print("Processing queries:")
    for query in queries:
        print(f"\n=== Query: {query} ===")
        result = engine.query(query)
        print(f"Result: {query} = {result}\n")


if __name__ == "__main__":
    sys.exit(main())
