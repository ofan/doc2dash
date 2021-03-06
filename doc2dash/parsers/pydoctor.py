import logging
import os

from bs4 import BeautifulSoup

from . import types
from .base import _BaseParser


log = logging.getLogger(__name__)


class PyDoctorParser(_BaseParser):

    """Parser for pydoctor-based documenation: mainly Twisted."""

    name = 'pydoctor'

    DETECT_FILE = 'index.html'
    DETECT_PATTERN = '''\
      This documentation was automatically generated by
      <a href="http://codespeak.net/~mwh/pydoctor/">pydoctor</a>'''

    def parse(self):
        """Parse pydoctor docs at *docpath*.

        yield tuples of symbol name, type and path

        """
        soup = BeautifulSoup(
            open(os.path.join(self.docpath, 'nameIndex.html')),
            'lxml'
        )
        log.info('Creating database...')
        for tag in soup.body.find_all('a'):
            path = tag.get('href')
            if path and not path.startswith('#'):
                name = tag.string
                yield name, _guess_type(name, path), path

    def find_and_patch_entry(self, soup, entry):
        link = soup.find('a', attrs={'name': entry.anchor})
        if link:
            tag = soup.new_tag('a')
            tag['name'] = self.APPLE_REF.format(entry.type, entry.name)
            link.insert_before(tag)
            return True
        else:
            return False


def _guess_type(name, path):
    """Employ voodoo magic to guess the type of *name* in *path*."""
    if name.rsplit('.', 1)[-1][0].isupper() and '#' not in path:
        return types.CLASS
    elif name.islower() and '#' not in path:
        return types.PACKAGE
    else:
        return types.METHOD
