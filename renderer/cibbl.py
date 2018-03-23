import re

def render(namespace):
  from renderer import default
  for t in namespace["teams"]:
    t["roster"]["name"] = re.sub('\s*\(.+$', '', t["roster"]["name"])
  return default.render(namespace)

