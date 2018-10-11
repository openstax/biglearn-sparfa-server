from io import BytesIO
from os import listdir


def path(name, mode='r'):
    return open('tests/json/{0}'.format(name), mode)


def content(path_name):
    content = path(path_name).read().strip()
    iterable = '[{0}]'.format(content)
    content = content.encode()
    iterable = iterable.encode()
    return BytesIO(content), BytesIO(iterable)


default = {}
iterable = {}
for file in os.listdir('tests/json/'):
    default[file], iterable[file] = content(file)
