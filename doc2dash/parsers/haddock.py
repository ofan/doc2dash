import logging
import os
import errno
import shutil
from urlparse import urlparse
from bs4 import BeautifulSoup
from . import types
from .base import _BaseParser

log = logging.getLogger(__name__)
FileCache = {}


def _remove_anchor(url):
    res = ''
    try:
        res = url[:url.index('#')]
    except:
        res = url
    return res.strip()


def _guess_type(url):
    anchor = urlparse(url).fragment
    if "t:" in anchor:
        return types.CLASS
    elif "v:" in anchor:
        return types.FUNCTION


def _link2dest(path, docpath, copy=False):
    if path[0] == '/':
        f = os.path.basename(path)
        p = os.path.join(docpath, _remove_anchor(f))
        if not os.path.exists(p):
            if not os.path.exists(os.path.dirname(p)):
                os.makedirs(os.path.dirname(p))
            if copy:
                try:
                    shutil.copyfile(path, p)
                except:
                    log.info("Cannot copy file %s to %s"
                             % (path, p))
            else:
                os.symlink(path, p)
        return f
    else:
        return path


def _fix_infix(n, t):
    init = n[0]
    if (t == types.FUNCTION and
            not init.isalpha() and
            init not in '_('):
        n = u'(%s)' % n
    return n


def _fix_links(soup):
    module = soup.find('div', id='module-header')\
        .find('p', attrs={'class': 'caption'}).string.strip()
    if module not in FileCache:
        FileCache[module] = True
        div = soup.find('div', id='content')
        for a in div.find_all('a', href=True):
            # Skip source links
            if a.string == 'Source':
                continue
            a['href'] = os.path.basename(a['href'])


class HaddockParser(_BaseParser):
    """ Parser for Haskell haddock documentation. """
    name = "haddock"
    DETECT_FILE = "haddock-util.js"
    DETECT_PATTERN = '''Haddock'''
    INDEX_FILES = ['doc-index-All.html', 'doc-index.html']

    def parse(self):
        """Parse haddock docs at *docpath*.
        yields tuples of symbol name, type and path
        """
        # Cache added module names to prevent duplicates
        modCache = {}
        for indexFile in HaddockParser.INDEX_FILES:
            try:
                soup = BeautifulSoup(open(os.path.join(self.docpath,
                                     indexFile)), 'lxml')
                break
            except IOError:
                pass
        else:
            raise IOError(errno.ENOENT, "Essential index file not found.")

        log.info('Creating database...')

        symName = ''
        symType = ''
        symPath = ''
        for tr in soup.body.find_all('tr'):
            for td in tr.find_all('td'):
                if 'class' not in td.attrs:
                    # Empty td entry, omit it
                    continue

                cl = td['class']
                if 'src' in cl:
                    symName = td.string.strip()
                    # Reached a new symbol name, reset type
                    symType = ''
                elif 'module' in cl:
                    modules = tr.find_all('a')
                    if len(modules) <= 0:
                        continue
                    for m in modules:
                        mName = m.string.strip()
                        symPath = m['href'].strip()
                        if mName not in modCache:
                            modCache[mName] = True
                            mPath = _link2dest(_remove_anchor(symPath),
                                               self.docpath, copy=False)
                            log.debug("Adding module: %s (%s) in '%s'"
                                      % (mName, types.PACKAGE, mPath))
                            yield mName, types.PACKAGE, mPath
                        if symName:
                            symType = _guess_type(symPath)
                            # Enclose infix operators by parentheses
                            symName = _fix_infix(symName, symType)
                            # Copy or link target file to Documents/
                            symPath = _link2dest(symPath, self.docpath,
                                                 copy=False)
                            log.debug("Adding symbol: %s (%s) in '%s'"
                                      % (symName, symType, symPath))
                            yield symName, symType, symPath

    def find_and_patch_entry(self, soup, entry):
        """ Verify whether the anchor is actually in the target file.
        """
        _fix_links(soup)
        return soup.find('a', attrs={'name': entry.anchor})
