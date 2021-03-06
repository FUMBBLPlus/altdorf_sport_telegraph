import collections


# https://stackoverflow.com/a/2912455/2334951
class keydefaultdict(collections.defaultdict):
  def __missing__(self, key):
    if self.default_factory is None:
      raise KeyError(key)
    else:
      ret = self[key] = self.default_factory(key)
      return ret
