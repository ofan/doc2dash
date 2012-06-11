import os

from bs4 import BeautifulSoup


def parse(path):
    """Parse pydoctor docs at *path*.

    yield tuples of symbol name, type and path

    """
    soup = BeautifulSoup(open(os.path.join(path, 'nameIndex.html')), 'lxml')
    print('Creating database...')
    for tag in soup.body.find_all('a'):
        path = tag.get('href')
        if path and not path.startswith('#'):
            name = tag.string.rsplit('.')[-1]
            yield name, _guess_type(name, path), os.path.join('data', path)


def _guess_type(name, path):
    """Employ voodoo magic to guess the type of *name* in *path*."""
    if name[0].isupper() and '#' not in path:
        return 'cl'
    elif name.islower() and '#' not in path:
        return 'cat'
    else:
        return 'clm'