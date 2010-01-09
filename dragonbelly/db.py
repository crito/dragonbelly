"""\
db.py  -  Handle a connection to a nosql backend

DBConnection returns a global instance. It contains a per domain index of the
file system structure. This index is used to search for files. A leaf of a
node is a bucket that contains file entries. Each file entry is a reference
to a key in the nosql backend. A domain can rebuild an index. The index is
always updated with each write operation and then also saved if wanted.
Otherwise its saved in a certain interval. These indexes are implemented using
B+tree's(?).

The key of a nosql object is the full path name of the file object. If the url
to the content is 

::
    http://static.domainA.org/upload/file.jpg 

the store object would look like that:

::
    store['/upload/file.jpg'] ==> {
        'locations': ['http://img1.domainA.org/path.file.jpg',
                      'http://img3.domainA.org/path/file.jpg'],
        'type': 'image/jpg',
    }
"""
from utils import Singleton

class DBConnection(Singleton):
    """\
    Top level interface to a global nosql backend.

    Goal is to provide a generic interface and implement the specific nosql engine
    function calls in plugins. it returns a global instance. Init() can take a
    callable for a db engine. Defaults to redis.

    >>> db = DBConnection()
    >>> db.listdb()
    []
    >>> db.newdb('domainA')
    >>> db[domainA].get()
    []
    >>> db[domainA].add(db_entry_object)
    >>> db.newdb('domainB')
    >>> db[domainA].clone(file_id, target_domain)
    >>> db.listdb()
    ['domainA', 'domainB']
    """

    # host status constants
    _DBUP = 0x0001
    _DBDOWN = 0x0002

    def __init__(self, db=None):
        self._dbbackend = db or _db_backend()
        self._dbengine = self._dbbackend.func_name
        self._domains = {}
        self._all_hosts = set()
        self._down_hosts = set()

    def newdb(self, domain):
        """Create a new db."""
        self._domains[domain.__str__()] = domain

    def listdb(self, domain):
        """List all db's."""
        [db for db in self._domains]

    def deldb(self, domain):
        """Delete a domain."""
        pass

class RedisDB(object):
    """\
    Handles connection to a redis backend.
    """
    pass


