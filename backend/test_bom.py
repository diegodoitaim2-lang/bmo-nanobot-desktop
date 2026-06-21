import json
from pathlib import Path
import sys
sys.path.insert(0, '.')
from bmo_backend import safe_read_text

# Teste 1: arquivo real
path = Path.home() / '.bmo' / 'nanobot' / 'subagents.json'
print('Arquivo existe:', path.exists())
data = json.loads(safe_read_text(path, '{}'))
print('Teste 1 - parse OK:', data.get('items'))

# Teste 2: simular arquivo COM BOM
import tempfile, os
with tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='wb') as f:
    f.write(b'\xef\xbb\xbf{"test": true}')
    fname = f.name
result = safe_read_text(Path(fname), '{}')
parsed = json.loads(result)
print('Teste 2 - BOM parse OK:', parsed)
os.unlink(fname)
print('Tudo OK')
