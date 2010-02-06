#! /usr/bin/env python

"""
"""

import sys, os

try:
    (backup_path,dest_path) = sys.argv[1:]
except IndexError:
    print "Usage: %s backup-dir new-photo-dir" % sys.argv[0]
    sys.exit(1)

os.mkdir(dest_path)
dest_prefix=os.path.abspath(dest_path)
os.chdir(backup_path)

# get the DB
home=os.environ.get('HOME',None)

os.spawnlp(os.P_WAIT, 'cp', 'cp', 'fspot.db', 'fspot-restored.db')

from pysqlite2 import dbapi2 as sqlite3

db = sqlite3.connect('fspot-restored.db')
c = db.cursor()

def backup_photo(uri):
    "Backup the photo, return the new uri"
    if not uri.startswith("file://"): raise ValueError, uri
    oldname=uri[7:]
    newname=os.path.join(dest_prefix,oldname)
    if os.spawnlp(os.P_WAIT, 'cp', 'cp', '-l', oldname, newname): raise ValueError, (oldname,newname)
    return 'file://'+newname
c.execute('''select id, uri from photos''')
new_photos = [(id, backup_photo(uri)) for id,uri in c]
c.execute('''select photo_id, version_id, uri from photo_versions where version_id <> 1''')
new_versions = [(pid, vid, backup_photo(uri)) for pid,vid,uri in c]
for id, uri in new_photos:
    c.execute("update photos set uri=? where id=?",(uri,id))
for id, uri in new_photos:
    c.execute("update photo_versions set uri=? where photo_id=? and version_id=1 ",(uri,id))
for pid, vid, uri in new_versions:
    c.execute("update photo_versions set uri=? where photo_id=? and version_id=? ",(uri,pid,vid))
    

db.commit()
db.close()

os.spawnlp(os.P_WAIT, 'cp', 'cp', 'fspot-restored.db', os.path.join(home,'.gnome2','f-spot','photos.db'))

print "restored F-Spot database"