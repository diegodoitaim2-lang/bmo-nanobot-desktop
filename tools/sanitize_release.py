#!/usr/bin/env python3
"""
sanitize_release.py — Remove referencias pessoais do codigo fonte e documentacao.

Modo de uso:
    python tools/sanitize_release.py          # preview (so mostra o que mudaria)
    python tools/sanitize_release.py --apply   # aplica as mudancas

Regras:
    - Nao modifica node_modules/, dist/, runtime/, .git/
    - Nao modifica arquivos binarios
    - Cria backup .pre-sanitize antes de modificar
    - Remove: DIEGO, PROJETO OPENCLAW, bmo-nanobot-desktop, C:\\Users, caminhos absolutos
"""

import os
import re
import sys
import shutil

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXCLUDE_DIRS = {
    "node_modules", "dist", "runtime", ".git", "__pycache__",
    "build", "electron-release", "data\\audit", "data\\packaged",
    "data\\packaged-onedir", "data\\toolcall-test",
    "_archive_cleanup", "_archive",
}
EXCLUDE_EXT = frozenset({
    ".exe", ".dll", ".bin", ".onnx", ".png", ".jpg", ".jpeg",
    ".wav", ".mp3", ".ico", ".zip", ".pyc",
})

REPLACEMENTS = [
    # (regex, replacement, description)
    (re.compile(r"\bDIEGO\b"), "USER", "nome de usuario"),
    (re.compile(r"PROJETO\s*OPENCLAW", re.IGNORECASE), "BMO_PROJECT", "nome do projeto"),
    (re.compile(r"bmo-nanobot-desktop"), "bmo", "nome do diretorio do projeto"),
    (re.compile(r"DESKTOP-6KAJT7D"), "BMO-HOST", "nome do host"),
    (re.compile(r"C:\\Users\\([^\\]+)", re.IGNORECASE), r"C:\\Users\\USER", "caminho home do usuario"),
]

# Arquivos que devem ser IGNORADOS (nao tocar)
SKIP_FILES = frozenset({
    "tools\\sanitize_release.py",
    ".nanobot\\config.json",
})

# Arquivos que devem ter BACKUP obrigatorio antes de modificar
BACKUP_EXT = frozenset({".py", ".ts", ".tsx", ".json", ".md", ".txt", ".css", ".html", ".ps1", ".yml", ".yaml"})


def should_skip(path: str) -> bool:
    rel = os.path.relpath(path, PROJECT)
    parts = rel.split(os.sep)
    for d in EXCLUDE_DIRS:
        if d in parts:
            return True
    ext = os.path.splitext(path)[1].lower()
    if ext in EXCLUDE_EXT:
        return True
    if rel in SKIP_FILES:
        return True
    return False


def is_binary(path: str) -> bool:
    try:
        with open(path, "rb") as f:
            return b"\x00" in f.read(1024)
    except Exception:
        return True


def scan_files() -> list[str]:
    targets = []
    for root, dirs, files in os.walk(PROJECT):
        if should_skip(root):
            continue
        for fname in files:
            fpath = os.path.join(root, fname)
            if should_skip(fpath):
                continue
            if is_binary(fpath):
                continue
            ext = os.path.splitext(fname)[1].lower()
            if ext not in BACKUP_EXT:
                continue
            targets.append(fpath)
    return targets


def sanitize_content(text: str) -> tuple[str, list[str]]:
    changes = []
    for pat, replacement, desc in REPLACEMENTS:
        new_text, count = pat.subn(replacement, text)
        if count > 0:
            changes.append(f"  {desc}: {count} substituicao(oes)")
            text = new_text
    return text, changes


def main():
    apply_mode = "--apply" in sys.argv
    targets = scan_files()

    total_changes = 0
    modified_files = []

    for fpath in sorted(targets):
        try:
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                original = f.read()
        except Exception as e:
            print(f"[SKIP] {os.path.relpath(fpath, PROJECT)} (erro leitura: {e})")
            continue

        sanitized, changes = sanitize_content(original)
        if not changes:
            continue

        total_changes += len(changes)
        rel = os.path.relpath(fpath, PROJECT)
        modified_files.append((rel, changes, original))

    if not modified_files:
        print("Nenhum arquivo com referencias pessoais encontrado.")
        return

    print(f"=== PREVIEW: {len(modified_files)} arquivo(s) seriam modificados ===")
    print(f"Total de substituicoes: {sum(len(c) for _, c, _ in modified_files)}")
    print()

    for rel, changes, original in modified_files:
        print(f"[{rel}]")
        for c in changes:
            print(f"  {c}")
        print()

    if not apply_mode:
        print("--- Preview mode. Use --apply para aplicar as mudancas. ---")
        return

    # APPLY
    backup_dir = os.path.join(PROJECT, "_backup_sanitize")
    os.makedirs(backup_dir, exist_ok=True)
    print(f"=== APLICANDO ({len(modified_files)} arquivos) ===")

    for rel, changes, original in modified_files:
        fpath = os.path.join(PROJECT, rel)
        # Backup
        backup_path = os.path.join(backup_dir, rel.replace("\\", "_").replace("/", "_"))
        try:
            shutil.copy2(fpath, backup_path)
        except Exception:
            pass

        sanitized, _ = sanitize_content(original)
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(sanitized)
        print(f"  [OK] {rel}")

    print(f"\nBackups salvos em: {backup_dir}")
    print("Para reverter: copie os arquivos de volta do diretorio de backup.")
    print("\n=== SANITIZACAO CONCLUIDA ===")


if __name__ == "__main__":
    main()
