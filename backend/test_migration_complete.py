"""
Teste integrado: verificar que a migracao de runtime unico funciona.

Testa SEM iniciar o servidor HTTP:
1. Import de todos os modulos
2. nanobot_integration tem todas as APIs
3. channels_list funciona
4. Nao ha chamadas a nanobot_bridge no bmo_backend
5. compileall passa em todos os arquivos
6. npm run build passa

Para testar chat real, memória e tools, o backend precisa estar rodando.
"""
import sys
import os
import subprocess

PROJETO = r"C:\Users\USER\Documents\BMO_PROJECT\bmo"
sys.path.insert(0, PROJETO)
sys.path.insert(0, os.path.join(PROJETO, "backend"))

errors = []

def check(name, condition, detail=""):
    if condition:
        print(f"  ✅ {name}")
    else:
        print(f"  ❌ {name} - {detail}")
        errors.append(name)

print("=" * 60)
print("TESTE DE MIGRACAO - RUNTIME UNICO")
print("=" * 60)
print()

# Teste 1: Import modules
print("[1] Import dos modulos")
try:
    from backend import nanobot_integration as ni
    from backend import nanobot_runtime as nr
    check("nanobot_integration importado", True)
    check("nanobot_runtime importado", True)
except Exception as e:
    check("Imports", False, str(e))

# Teste 2: nanobot_integration API completa
print()
print("[2] nanobot_integration API")
for attr in ['chat', 'is_runtime_ready', 'runtime_status', 'initialize_runtime',
             'tool_definitions', 'execute_tool', 'tool_names', 'tool_info',
             'memory_payload', 'append_history', 'spawn_subagent',
             'channels_list', 'invalidate_runtime']:
    check(f"ni.{attr}", hasattr(ni, attr))

# Teste 3: nanobot_runtime API completa
print()
print("[3] nanobot_runtime API")
nr_cls = nr.NanobotRuntime
for attr in ['initialize', 'get_instance', 'reset', 'chat', 'execute_tool',
             'definitions', 'tool_info', 'append_history', 'memory_payload',
             'spawn_subagent', 'channels_list', 'invalidate', 'status', 'close']:
    check(f"nr.NanobotRuntime.{attr}", hasattr(nr_cls, attr))

# Teste 4: nanobot_integration runtime_status funciona
print()
print("[4] runtime_status (sem inicializar)")
status = ni.runtime_status()
check("runtime_status retorna dict", isinstance(status, dict))
check("status tem 'ready'", 'ready' in status)
check("status tem 'error'", 'error' in status)

# Teste 5: channels_list
print()
print("[5] channels_list")
try:
    channels = ni.channels_list()
    check("channels_list retorna lista", isinstance(channels, list))
    check(f"canais encontrados: {len(channels)}", len(channels) > 0)
    if channels:
        check("canais tem 'id'", 'id' in channels[0])
        check("canais tem 'label'", 'label' in channels[0])
except Exception as e:
    check("channels_list funcionou", False, str(e))

# Teste 6: nanobot_bridge removido do bmo_backend.py
print()
print("[6] Bridge removido")
with open(os.path.join(PROJETO, "backend", "bmo_backend.py"), 'r') as f:
    content = f.read()
bridge_calls = 0
for line in content.split('\n'):
    if 'nanobot_bridge.' in line:
        bridge_calls += 1
check("0 chamadas a nanobot_bridge.", bridge_calls == 0, f"ainda tem {bridge_calls}")

# Teste 7: compileall
print()
print("[7] Python compileall")
result = subprocess.run(
    [sys.executable, "-m", "compileall", os.path.join(PROJETO, "backend")],
    capture_output=True, text=True, timeout=30
)
compile_ok = result.returncode == 0
check("compileall backend OK", compile_ok, result.stderr[:200] if result.stderr else "")

# Teste 8: npm run build
print()
print("[8] npm run build")
result = subprocess.run(
    ["npm", "run", "build"],
    cwd=PROJETO,
    capture_output=True, text=True, timeout=60
)
build_ok = result.returncode == 0 and "built in" in result.stdout
check("npm run build OK", build_ok, result.stderr[:200] if result.stderr else "")

# Teste 9: Verificar que nanobot_bridge ainda existe em deprecated/
print()
print("[9] Bridge em deprecated/")
bridge_path = os.path.join(PROJETO, "backend", "deprecated", "nanobot_bridge.py")
check("nanobot_bridge.py existe em deprecated/", os.path.exists(bridge_path))

# Teste 10: Verificar que nao ha duplicatas de definitions
print()
print("[10] Sem duplicatas de definitions")
with open(os.path.join(PROJETO, "backend", "nanobot_runtime.py"), 'r') as f:
    rt_content = f.read()
count_def = rt_content.count("def definitions(self)")
check("definitions aparece 1 vez", count_def == 1, f"aparece {count_def} vezes")

# Resumo
print()
print("=" * 60)
print(f"RESULTADO: {len(errors)} falha(s) em 10 testes")
if errors:
    print(f"Falhas: {', '.join(errors)}")
else:
    print("✅ TODOS OS TESTES PASSARAM")
print("=" * 60)
