"""Launcher para testar o backend BMO original restaurado."""
import sys
import os

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend = os.path.join(root, 'backend')

sys.path.insert(0, root)
sys.path.insert(0, backend)

os.environ.setdefault('BMO_HOME', os.path.join(os.path.expanduser('~'), '.bmo'))

from bmo_backend import main
main()
