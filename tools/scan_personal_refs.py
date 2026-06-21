#!/usr/bin/env python3
"""Scan active project files for personal references."""

import os, re, sys

PROJECT = r"C:\Users\USER\Documents\BMO_PROJECT\bmo"
EXCLUDE_DIRS = {
    "node_modules", "dist", "runtime", ".git", "__pycache__",
    "data\\audit", "data\\packaged", "data\\packaged-onedir",
    "data\\toolcall-test", "build", "electron-release",
    "_archive_cleanup", "_archive", "BMO_RELATORIO",
    ".easyclaw", "easyclaw",
}
EXCLUDE_EXT = {".exe", ".dll", ".bin", ".onnx", ".png", ".jpg", ".jpeg",
               ".wav", ".mp3", ".ico", ".zip", ".pyc", ".gitkeep"}

PATTERNS = [
    ("USER", re.compile(r"\bDIEGO\b")),
    ("BMO_PROJECT", re.compile(r"PROJETO\s*OPENCLAW", re.IGNORECASE)),
    ("bmo", re.compile(r"bmo")),
    ("BMO-HOST", re.compile(r"BMO-HOST")),
    ("C:\\Users", re.compile(r"C:\\Users", re.IGNORECASE)),
]

results = {name: {} for name, _ in PATTERNS}

for root, dirs, files in os.walk(PROJECT):
    # Skip excluded dirs
    rel = os.path.relpath(root, PROJECT)
    parts = rel.split(os.sep)
    if any(d in parts for d in EXCLUDE_DIRS):
        continue
    if any(d in rel for d in EXCLUDE_DIRS):
        continue

    for fname in files:
        ext = os.path.splitext(fname)[1].lower()
        if ext in EXCLUDE_EXT:
            continue
        fpath = os.path.join(root, fname)
        rel_path = os.path.relpath(fpath, PROJECT)
        try:
            with open(fpath, "rb") as f:
                raw = f.read()
        except Exception:
            continue
        # Skip truly binary files
        if b"\x00" in raw[:1024]:
            continue
        text = raw.decode("utf-8", errors="replace")

        for name, pat in PATTERNS:
            if pat.search(text):
                results[name][rel_path] = results[name].get(rel_path, 0) + 1

for name, files in results.items():
    if not files:
        print(f"[{name}] NENHUMA OCORRENCIA")
    else:
        print(f"[{name}] {len(files)} arquivo(s):")
        for f, count in sorted(files.items()):
            print(f"    {f} ({count} ocorrencia(s))")

total = sum(len(v) for v in results.values())
print(f"\n--- TOTAL: {total} arquivos com referencias pessoais ---")
