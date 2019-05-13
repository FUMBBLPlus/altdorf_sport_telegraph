from renderer import noroster

EXTRA_STRIP = '- ⠀'


def render(namespace):
  status = namespace['status'].upper()
  fstr = getattr(noroster, status)
  namespace["time"] = ':'.join(namespace["time"].split(':')[:2])
  for t in namespace["teams"]:
    t["name"] = t["name"].strip(EXTRA_STRIP)
  return fstr.format(**namespace)

