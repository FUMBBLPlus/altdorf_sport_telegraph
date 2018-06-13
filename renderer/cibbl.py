import re

from renderer import default


def render(namespace):
  for t in namespace["teams"]:
    t["roster"]["name"] = re.sub('\s*\(.+$', '', t["roster"]["name"])
  return default.render(namespace)

