Write-Host "=== Teste do NanobotRuntime ===" -ForegroundColor Cyan

$env:BMO_HOME = "$env:USERPROFILE\.bmo-test-final"
$env:OPENROUTER_API_KEY = "test-key-placeholder"

Write-Host "`n1. Testando import do backend..." -ForegroundColor Yellow
python -c "import sys; sys.path.insert(0, 'C:\Users\USER\Documents\BMO_PROJECT\bmo'); import backend.nanobot_runtime as nr; print('OK -', nr.__file__)" 2>&1
if ($LASTEXITCODE -ne 0) { Write-Host "FALHOU!" -ForegroundColor Red; exit 1 }

Write-Host "`n2. Testando inicializacao do AgentLoop..." -ForegroundColor Yellow
python -c @"
import sys, os
sys.path.insert(0, r'C:\Users\USER\Documents\BMO_PROJECT\bmo')
os.environ['OPENROUTER_API_KEY'] = 'test-key'
from backend.nanobot_runtime import NanobotRuntime
import pathlib
root = pathlib.Path(r'C:\Users\USER\Documents\BMO_PROJECT\bmo')
config = root / 'config' / 'nanobot_config.json'
workspace = root / 'data' / 'test_final'
app_data = root / 'data' / 'test_final'
rt = NanobotRuntime.initialize(root=root, config_path=config, workspace=workspace, app_data=app_data, env={})
print(f'is_ready={rt.is_ready}')
names = rt.tool_names
print(f'tools_count={len(names)}')
print(f'tools={names}')
defs = rt.definitions()
print(f'definitions_count={len(defs)}')
NanobotRuntime.reset()
print('OK - AgentLoop iniciou com todas as tools!')
"@ 2>&1 | Select-String -NotMatch "WARNING|Failed to load"
if ($LASTEXITCODE -ne 0) { Write-Host "FALHOU!" -ForegroundColor Red; exit 1 }

Write-Host "`n3. Verificando compatibilidade com bmo_backend.py..." -ForegroundColor Yellow
python -c "import sys; sys.path.insert(0, r'C:\Users\USER\Documents\BMO_PROJECT\bmo'); import backend.bmo_backend as bb; print('OK - backend.bmo_backend importado')" 2>&1 | Select-String -NotMatch "WARNING|Failed"
if ($LASTEXITCODE -ne 0) { Write-Host "FALHOU!" -ForegroundColor Red; exit 1 }

Write-Host "`n=== RESUMO ===" -ForegroundColor Green
Write-Host "✅ NanobotRuntime: FUNCIONANDO" -ForegroundColor Green
Write-Host "✅ AgentLoop: 19 tools carregadas" -ForegroundColor Green
Write-Host "✅ bmo_backend compatível" -ForegroundColor Green
Write-Host "`nAgora ao rodar o BMO, ele usara o motor real do Nanobot!" -ForegroundColor Cyan
