from dateutil.tz import tzfile
from tarfile import TarFile
import os

__all__ = ["setcachesize", "gettz", "rebuild"]

CACHE = []
CACHESIZE = 10

ZONEINFOFILE = None
for entry in os.listdir(os.path.dirname(__file__)):
    if entry.startswith("zoneinfo") and ".tar." in entry:
        ZONEINFOFILE = os.path.join(os.path.dirname(__file__), entry)
        break

def setcachesize(size):
    global CACHESIZE, CACHE
    CACHESIZE = size
    del CACHE[size:]

def gettz(name):
    tzinfo = None
    if ZONEINFOFILE:
        for cachedname, tzinfo in CACHE:
            if cachedname == name:
                break
        else:
            tf = TarFile.open(ZONEINFOFILE)
            try:
                zonefile = tf.extractfile(name)
            except KeyError:
                tzinfo = None
            else:
                tzinfo = tzfile(zonefile)
            tf.close()
            CACHE.insert(0, (name, tzinfo))
            del CACHE[CACHESIZE:]
    return tzinfo

def rebuild(filename, tag=None):
    import tempfile, shutil
    tmpdir = tempfile.mkdtemp()
    zonedir = os.path.join(tmpdir, "zoneinfo")
    moduledir = os.path.dirname(__file__)
    if tag: tag = "-"+tag
    targetname = "zoneinfo%s.tar.bz2" % tag
    try:
        tf = TarFile.open(filename)
        for name in tf.getnames():
            if not (name.endswith(".sh") or
                    name.endswith(".tab") or
                    name == "leapseconds"):
                tf.extract(name, tmpdir)
                filepath = os.path.join(tmpdir, name)
                os.system("zic -d %s %s" % (zonedir, filepath))
        tf.close()
        target = os.path.join(moduledir, targetname)
        for entry in os.listdir(moduledir):
            if entry.startswith("zoneinfo") and entry.endswith(".tar.bz2"):
                os.unlink(os.path.join(moduledir, entry))
        tf = TarFile.open(target, "w:bz2")
        for entry in os.listdir(zonedir):
            entrypath = os.path.join(zonedir, entry)
            tf.add(entrypath, entry)
        tf.close()
    finally:
        shutil.rmtree(tmpdir)
