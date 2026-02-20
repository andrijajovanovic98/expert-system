#!/usr/bin/env python3
# *************************************************************************** #
#                                                                             #
#                                                        :::      ::::::::    #
#   knowledge_graph.py                                 :+:      :+:    :+:    #
#                                                    +:+ +:+         +:+      #
#   By: iberegsz <iberegsz@student.42vienna.com>   +#+  +:+       +#+         #
#                                                +#+#+#+#+#+   +#+            #
#   Created: 2026/01/18 21:37:16 by iberegsz          #+#    #+#              #
#   Updated: 2026/01/23 01:43:21 by iberegsz         ###   ########.fr        #
#                                                                             #
# *************************************************************************** #

"""
Knowledge Graph - Global graph of fact nodes linked by rule nodes.

This module implements a level-5 data structure for expert system:
- Explicit FactGraphNode and RuleGraphNode objects
- Bidirectional edges between facts and rules
- O(1) lookup for rules concluding a fact
- O(1) lookup for facts used in rule conditions
- Graph traversal capabilities for proof visualization and analysis
"""

from typing import Set, List, Dict, Optional
from dataclasses import dataclass, field
from parser import Rule, ASTNode


@dataclass
class FactGraphNode:
    """
    Represents a fact in the knowledge graph.

    Contains bidirectional links to rules that:
    - Use this fact in their condition (incoming_rules)
    - Conclude this fact (concluding_rules)
    """
    fact: str
    is_initial: bool = False

    concluding_rules: Set['RuleGraphNode'] = field(default_factory=set)

    used_by_rules: Set['RuleGraphNode'] = field(default_factory=set)

    def __hash__(self):
        return hash(self.fact)

    def __eq__(self, other):
        if isinstance(other, FactGraphNode):
            return self.fact == other.fact
        return False

    def __repr__(self):
        initial_marker = " (initial)" if self.is_initial else ""
        return f"FactNode({self.fact}{initial_marker})"


@dataclass
class RuleGraphNode:
    """
    Represents a rule in the knowledge graph.

    Contains bidirectional links to facts:
    - Facts used in the condition (condition_facts)
    - Facts that can be concluded (conclusion_facts)
    """
    rule_id: int
    rule: Rule

    condition_facts: Set[FactGraphNode] = field(default_factory=set)

    conclusion_facts: Set[FactGraphNode] = field(default_factory=set)

    def __hash__(self):
        return hash(self.rule_id)

    def __eq__(self, other):
        if isinstance(other, RuleGraphNode):
            return self.rule_id == other.rule_id
        return False

    def __repr__(self):
        return f"RuleNode(R{self.rule_id})"


class KnowledgeGraph:
    """
    Global knowledge graph linking facts and rules.

    Structure:
    - fact_nodes: Dict[str, FactGraphNode] - all facts in the system
    - rule_nodes: List[RuleGraphNode] - all rules in the system
    - Bidirectional edges maintained automatically

    Benefits:
    - O(1) lookup of rules concluding a fact
    - O(1) lookup of facts used by a rule
    - O(1) lookup of rules using a fact
    - Easy graph traversal for proofs, cycles, dependencies
    - Metadata storage per node (initial facts, rule IDs)
    """

    def __init__(self, rules: List[Rule], initial_facts: Set[str]):
        self.fact_nodes: Dict[str, FactGraphNode] = {}
        self.rule_nodes: List[RuleGraphNode] = []
        self.initial_facts = initial_facts

        self._build_graph(rules, initial_facts)

    def _build_graph(self, rules: List[Rule], initial_facts: Set[str]):
        """Build the global knowledge graph from rules and facts."""
        all_facts = set(initial_facts)
        for rule in rules:
            all_facts.update(rule.get_all_facts())

        for fact in all_facts:
            self.fact_nodes[fact] = FactGraphNode(
                fact=fact,
                is_initial=(fact in initial_facts)
            )

        for idx, rule in enumerate(rules):
            self._add_rule(idx, rule)

    def _add_rule(self, rule_id: int, rule: Rule):
        """Add a rule to the graph with proper linking."""
        rule_node = RuleGraphNode(rule_id=rule_id, rule=rule)

        if rule.is_biconditional:
            self._link_rule_direction(
                rule_node,
                rule.condition,
                rule.conclusion,
                rule_id * 2
            )

            reverse_node = RuleGraphNode(
                rule_id=rule_id * 2 + 1,
                rule=Rule(rule.conclusion, rule.condition, False)
            )
            self._link_rule_direction(
                reverse_node,
                rule.conclusion,
                rule.condition,
                rule_id * 2 + 1
            )
            self.rule_nodes.append(reverse_node)
        else:
            self._link_rule_direction(
                rule_node,
                rule.condition,
                rule.conclusion,
                rule_id
            )

        self.rule_nodes.append(rule_node)

    def _link_rule_direction(
        self,
        rule_node: RuleGraphNode,
        condition: ASTNode,
        conclusion: ASTNode,
        rule_id: int
    ):
        """Link a rule's condition facts and conclusion facts."""
        condition_fact_names = condition.get_facts()
        for fact_name in condition_fact_names:
            if fact_name not in self.fact_nodes:
                self.fact_nodes[fact_name] = FactGraphNode(fact=fact_name)

            fact_node = self.fact_nodes[fact_name]

            rule_node.condition_facts.add(fact_node)
            fact_node.used_by_rules.add(rule_node)

        concluded_fact_names = self._get_concluded_facts(conclusion)
        for fact_name in concluded_fact_names:
            if fact_name not in self.fact_nodes:
                self.fact_nodes[fact_name] = FactGraphNode(fact=fact_name)

            fact_node = self.fact_nodes[fact_name]

            rule_node.conclusion_facts.add(fact_node)
            fact_node.concluding_rules.add(rule_node)

    def _get_concluded_facts(self, node: ASTNode) -> Set[str]:
        """Extract facts that can be concluded from a conclusion node."""
        from parser import FactNode, UnaryOpNode, BinaryOpNode, NodeType

        if isinstance(node, FactNode):
            return {node.fact}
        elif isinstance(node, UnaryOpNode) and node.node_type == NodeType.NOT:
            if isinstance(node.operand, FactNode):
                return {f"!{node.operand.fact}"}
            return set()
        elif isinstance(node, BinaryOpNode):
            if node.node_type in (NodeType.AND, NodeType.OR, NodeType.XOR):
                return (self._get_concluded_facts(node.left) |
                        self._get_concluded_facts(node.right))
        return set()

    def get_fact_node(self, fact: str) -> Optional[FactGraphNode]:
        """Get fact node by name."""
        return self.fact_nodes.get(fact)

    def get_rules_concluding(self, fact: str) -> Set[RuleGraphNode]:
        """Get all rules that can conclude a fact (O(1) lookup)."""
        fact_node = self.fact_nodes.get(fact)
        if fact_node:
            return fact_node.concluding_rules
        return set()

    def get_rules_using(self, fact: str) -> Set[RuleGraphNode]:
        """Get all rules that use a fact in their condition (O(1) lookup)."""
        fact_node = self.fact_nodes.get(fact)
        if fact_node:
            return fact_node.used_by_rules
        return set()

    def is_initial_fact(self, fact: str) -> bool:
        """Check if a fact is an initial fact."""
        fact_node = self.fact_nodes.get(fact)
        return fact_node.is_initial if fact_node else False

    def get_all_facts(self) -> Set[str]:
        """Get all facts in the graph."""
        return set(self.fact_nodes.keys())

    def get_dependency_chain(self, fact: str) -> Set[str]:
        """Get all facts that a given fact depends on (transitive)."""
        visited = set()
        to_visit = {fact}

        while to_visit:
            current = to_visit.pop()
            if current in visited:
                continue
            visited.add(current)

            for rule_node in self.get_rules_concluding(current):
                for fact_node in rule_node.condition_facts:
                    if fact_node.fact not in visited:
                        to_visit.add(fact_node.fact)

        visited.discard(fact)
        return visited

    def __repr__(self):
        return (f"KnowledgeGraph(facts={len(self.fact_nodes)}, "
                f"rules={len(self.rule_nodes)})")
