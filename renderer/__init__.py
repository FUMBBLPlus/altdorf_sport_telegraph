import pathlib

for p in pathlib.Path(__file__).parent.glob('*.py'):
  if p.stem.startswith('_'):
    continue
  exec(f'from . import {p.stem}')

def render(namespace, renderer=None):
  if not renderer:
    m = globals()['default']
  else:
    m = globals()[renderer]
  return m.render(namespace)
