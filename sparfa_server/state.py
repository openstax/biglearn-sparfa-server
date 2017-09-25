# super simple state key-store thing

_state = {}

def set(topic, **kwargs):

  if _state.get(topic) is None:
    _state[topic] = {}

  _state[topic].update(dict(kwargs))  

  return get(topic)


def get(topic):

  return _state[topic]

