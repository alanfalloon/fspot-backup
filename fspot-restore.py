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

newdbfilename = os.path.join(dest_prefix,'fspot-restored.db')
os.spawnlp(os.P_WAIT, 'cp', 'cp', 'fspot.db', newdbfilename)

from pysqlite2 import dbapi2 as sqlite3

db = sqlite3.connect(newdbfilename)
c = db.cursor()

def backup_photo(uri):
    "Backup the photo, return the new uri"
    if not uri.startswith("file://"): raise ValueError, uri
    oldname=uri[7:]
    newname=os.path.join(dest_prefix,oldname)
    (newdirname,newbasename)=os.path.split(newname)
    if newdirname:
        newdirname = newdirname+"/"
        if os.spawnlp(os.P_WAIT, 'mkdir', 'mkdir', '-p', newdirname):
            raise ValueError, newdirname
    if os.spawnlp(os.P_WAIT, 'cp', 'cp', '-l', oldname, newname): raise ValueError, (oldname,newname)
    return ('file://'+newdirname, newbasename)
c.execute('''select id, base_uri, filename from photos''')
new_photos = [(id, backup_photo(uri+fn)) for id,uri,fn in c]
c.execute('''select photo_id, version_id, base_uri, filename from photo_versions where version_id <> 1''')
new_versions = [(pid, vid, backup_photo(uri+fn)) for pid,vid,uri,fn in c]
for id, (uri, fn) in new_photos:
    c.execute("update photos set base_uri=?, filename=? where id=?",(uri,fn,id))
for id, (uri, fn) in new_photos:
    c.execute("update photo_versions set base_uri=?, filename=? where photo_id=? and version_id=1 ",(uri,fn,id))
for pid, vid, (uri, fn) in new_versions:
    c.execute("update photo_versions set base_uri=?, filename=? where photo_id=? and version_id=? ",(uri,fn,pid,vid))
    

db.commit()
db.close()

print """To complete the restoration, run the following command:
cp %s ~/.config/f-spot/photos.db""" % (newdbfilename,)
