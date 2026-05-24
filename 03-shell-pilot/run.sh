#!/bin/bash
echo "=== shell-pilot demo ==="
echo ""
echo "Task 1: Count lines of code"
python agent.py "count the total number of lines of Python code in the current directory, excluding __pycache__"
echo ""
echo "Task 2: Find TODO comments"
python agent.py "find any TODO or FIXME comments in the Python files here and list them with their file and line number"
