#!/usr/bin/env python3
"""Check syntax of bmo_backend.py and find triple-quote imbalance."""
import sys

path = r'C:\Users\USER\Documents\BMO_PROJECT\bmo\backend\bmo_backend.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Check triple-quote balance line by line
open_count = 0
for i, line in enumerate(lines):
    line_num = i + 1
    # Count """ sequences (simple approach)
    idx = 0
    while True:
        idx = line.find('"""', idx)
        if idx == -1:
            break
        open_count += 1
        idx += 3
    if open_count % 2 != 0:
        print(f'Line {line_num}: UNBALANCED triple-quote (after line, cnt={open_count})')
        print(f'  {repr(line[:120])}')

print(f'\nTotal triple-quote occurrences: {open_count}')
if open_count % 2 == 0:
    print('OK - Balanced!')
else:
    print('UNBALANCED!')

# Now try ast.parse
import ast
try:
    with open(path, 'r', encoding='utf-8') as f:
        data = f.read()
    ast.parse(data)
    print('ast.parse: OK')
except SyntaxError as e:
    print(f'ast.parse error at line {e.lineno}: {e.msg}')
    if e.lineno and e.lineno <= len(lines):
        print(f'  Context: {repr(lines[e.lineno - 1][:150])}')
        if e.lineno < len(lines):
            print(f'  Next:    {repr(lines[e.lineno][:150])}')
