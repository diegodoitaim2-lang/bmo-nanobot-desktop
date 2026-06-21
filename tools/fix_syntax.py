#!/usr/bin/env python3
"""Fix syntax errors in bmo_backend.py - remove BMO_SYSTEM_PROMPT and balance triple quotes."""
import re

path = r'C:\Users\USER\Documents\BMO_PROJECT\bmo\backend\bmo_backend.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find BMO_SYSTEM_PROMPT line
bmo_start = None
for i, line in enumerate(lines):
    if 'BMO_SYSTEM_PROMPT' in line:
        bmo_start = i
        break

if bmo_start is not None:
    # Find next def after it
    next_def = None
    for i in range(bmo_start + 1, len(lines)):
        if lines[i].strip().startswith('def '):
            next_def = i
            break
    
    if next_def is not None:
        print(f'Removing BMO_SYSTEM_PROMPT lines {bmo_start+1} to {next_def}')
        del lines[bmo_start:next_def]
        print(f'Removed {next_def - bmo_start} lines')
    else:
        # If no def found, BMO_SYSTEM_PROMPT goes to end - remove from bmo_start to before last lines
        print(f'Removing BMO_SYSTEM_PROMPT from line {bmo_start+1} to end-5')
        del lines[bmo_start:-5]

# Also find DEFAULT_SOUL_MD if it exists
for i, line in enumerate(lines):
    if 'DEFAULT_SOUL_MD' in line and '=' in line:
        # Find its end (next def)
        next_def = None
        for j in range(i + 1, len(lines)):
            if lines[j].strip().startswith('def ') or lines[j].strip().startswith('#'):
                if j > i + 1:
                    next_def = j
                    break
        if next_def is not None:
            print(f'Removing DEFAULT_SOUL_MD lines {i+1} to {next_def}')
            del lines[i:next_def]
        break

# Remove the docstring handle_chat that has """ causing imbalance
for i, line in enumerate(lines):
    if '"""Processa mensagem de chat' in line:
        lines[i] = lines[i].replace('"""Processa mensagem de chat usando o AgentLoop real do Nanobot."""', '')
        print(f'Fixed handle_chat docstring at line {i+1}')
        break

# Write result
output = ''.join(lines)
with open(path, 'w', encoding='utf-8') as f:
    f.write(output)

# Validate
import ast
try:
    ast.parse(output)
    print('SYNTAX OK!')
except SyntaxError as e:
    print(f'Still broken at line {e.lineno}: {e.msg}')
    print(f'  Text: {repr(output.split(chr(10))[e.lineno-1])}')
