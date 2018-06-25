import re

from renderer import default
from renderer import noround

EXTRA_STRIP = '⠀'

def render(namespace):
  if "winter" in namespace["tournament"]["name"].lower():
    renderer_module = noround
  else:
    renderer_module = default
  for t in namespace["teams"]:
    t["roster"]["name"] = re.sub('\s*\(.+$', '', t["roster"]["name"])
    t["roster"]["name"] = t["roster"]["name"].strip(EXTRA_STRIP)
  return renderer_module.render(namespace)
