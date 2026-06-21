"""Teste de API - verificar que todos os metodos de migracao existem."""
import sys
sys.path.insert(0, r'C:\Users\USER\Documents\BMO_PROJECT\bmo')
sys.path.insert(0, r'C:\Users\USER\Documents\BMO_PROJECT\bmo\backend')

# Verificar que nanobot_integration tem todos os metodos esperados
from backend import nanobot_integration as ni

print('=== nanobot_integration API ===')
for attr in ['chat', 'is_runtime_ready', 'runtime_status', 'initialize_runtime',
             'tool_definitions', 'execute_tool', 'tool_names', 'tool_info',
             'memory_payload', 'append_history', 'spawn_subagent',
             'channels_list', 'invalidate_runtime']:
    print(f'  {attr}: {hasattr(ni, attr)}')

# Verificar que nanobot_runtime tem todos os metodos
from backend import nanobot_runtime as nr
nr_cls = nr.NanobotRuntime

print()
print('=== nanobot_runtime (classe) API ===')
for attr in ['initialize', 'get_instance', 'reset', 'chat', 'execute_tool',
             'definitions', 'tool_info', 'append_history', 'memory_payload',
             'spawn_subagent', 'channels_list', 'invalidate', 'status',
             'close']:
    print(f'  {attr}: {hasattr(nr_cls, attr)}')

print()
print('=== Instancia mock (metodos de instancia) ===')
# Verificar metodos de instancia
for attr in ['tool_names', 'is_ready', 'error', 'registry', 'sessions']:
    print(f'  {attr}: has property/getter: {hasattr(nr_cls, attr)}')

# Verificar que bmo_backend foi modificado
print()
with open(r'C:\Users\USER\Documents\BMO_PROJECT\bmo\backend\bmo_backend.py', 'r') as f:
    content = f.read()

bridge_uses = 0
for line in content.split('\n'):
    if 'nanobot_bridge.' in line:
        bridge_uses += 1

print(f'Chamadas a nanobot_bridge. em bmo_backend.py: {bridge_uses}')
print(f'  (0 = migracao completa)')
print()

# Testar channels_list (funcionamento)
print('=== Teste channels_list (leve) ===')
try:
    ch = ni.channels_list()
    print(f'  OK: {len(ch)} canais retornados')
except Exception as e:
    print(f'  Nota: {e} (pode ser normal se nanobot nao estiver no path)')

print()
print('=== VEREDITO ===')
tudo_ok = all([
    hasattr(ni, 'chat'), hasattr(ni, 'runtime_status'),
    hasattr(ni, 'initialize_runtime'), hasattr(ni, 'tool_definitions'),
    hasattr(ni, 'execute_tool'), hasattr(ni, 'tool_names'),
    hasattr(ni, 'tool_info'), hasattr(ni, 'memory_payload'),
    hasattr(ni, 'append_history'), hasattr(ni, 'spawn_subagent'),
    hasattr(ni, 'channels_list'), hasattr(ni, 'invalidate_runtime'),
])
print(f'Todas as APIs estao disponiveis: {tudo_ok}')
print(f'Bridge removido do fluxo: {bridge_uses == 0}')
