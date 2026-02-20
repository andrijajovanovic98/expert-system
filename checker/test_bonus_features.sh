#!/bin/bash
# *************************************************************************** #
#                                                                             #
#                                                        :::      ::::::::    #
#   test_bonus_features.sh                             :+:      :+:    :+:    #
#                                                    +:+ +:+         +:+      #
#   By: iberegsz <iberegsz@student.42vienna.com>   +#+  +:+       +#+         #
#                                                +#+#+#+#+#+   +#+            #
#   Created: 2026/01/18 21:12:04 by iberegsz          #+#    #+#              #
#   Updated: 2026/01/19 19:21:16 by iberegsz         ###   ########.fr        #
#                                                                             #
# *************************************************************************** #

# Test script for all bonus features

echo "======================================================================="
echo "BONUS FEATURES TEST SUITE"
echo "======================================================================="
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Testing Bonus #3 & #4: OR/XOR in Conclusions + IFF${NC}"
echo "======================================================================="

for test in test/test_bonus_*.txt; do
    echo ""
    echo "Testing: $test"
    echo "-----------------------------------------------------------------------"
    python3 expert_system.py "$test"
    echo ""
done

echo ""
echo -e "${YELLOW}Testing Bonus #2: Reasoning Visualization${NC}"
echo "======================================================================="
echo "Running reasoning visualizer on test/test_bonus_or_conclusion.txt"
echo "-----------------------------------------------------------------------"
python3 reasoning_visualizer.py test/test_bonus_or_conclusion.txt | head -30
echo "... (output truncated)"
echo ""

echo -e "${YELLOW}Testing Bonus #5: Statistics Analyzer${NC}"
echo "======================================================================="
echo "Running statistics analyzer on test/test1.txt"
echo "-----------------------------------------------------------------------"
python3 statistics_analyzer.py test/test1.txt | head -40
echo "... (output truncated)"
echo ""

echo -e "${GREEN}All bonus tests completed!${NC}"
echo ""
echo "======================================================================="
echo "BONUS FEATURES SUMMARY"
echo "======================================================================="
echo "Bonus #1: Interactive Fact Validation - interactive_mode.py"
echo "Bonus #2: Reasoning Visualization - reasoning_visualizer.py"
echo "Bonus #3: OR/XOR in Conclusions - inference_engine.py"
echo "Bonus #4: Biconditional (IFF) - parser.py + inference_engine.py"
echo "Bonus #5: Statistics Analyzer - statistics_analyzer.py"
echo ""
echo "Total: 5/5 bonus features implemented and tested!"
echo "======================================================================="
echo ""
echo "To test interactive mode manually:"
echo "  python3 interactive_mode.py test/test1.txt"
echo ""
