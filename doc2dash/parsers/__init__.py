from . import pydoctor, sphinx, haddock


DOCTYPES = [sphinx.SphinxParser, pydoctor.PyDoctorParser, haddock.HaddockParser]


def get_doctype(path):
    """Gets the apropriate doctype for *path*."""
    for dt in DOCTYPES:
        if dt.detect(path):
            return dt
    else:
        return None
