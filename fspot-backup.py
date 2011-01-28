#! /usr/bin/env python

"""
"""

import sys, os
import urllib
import EXIF

photonum=0
def get_new_image_name(img,ver):
    global photonum
    f = open(img, 'rb')
    try:
        tags = EXIF.process_file(f, strict=True, stop_tag="DateTimeOriginal")
        if "EXIF DateTimeOriginal" not in tags:
            photonum += 1
            return "photo%04d" % (photonum,)
        d = tags["EXIF DateTimeOriginal"]
        (day,time) = str(d).split()
        (y,m,d) = day.split(":")
        (H,M,S) = time.split(":")
        v=""
        if ver > 1:
            v="_v%d"%(ver,)
        return "%s/%s/%s/%s-%s-%s%s" % (y,m,d,H,M,S,v)
        
    finally:
        f.close()

try:
    dest_path = sys.argv[1]
except IndexError:
    print "directory name required"
    sys.exit(1)

os.mkdir(dest_path)
os.chdir(dest_path)

# get the DB
home=os.environ.get('HOME',None)

os.spawnlp(os.P_WAIT, 'cp', 'cp', os.path.join(home,'.config','f-spot','photos.db'), 'fspot.db')

print "copied F-Spot database"

from pysqlite2 import dbapi2 as sqlite3

db = sqlite3.connect('fspot.db')
c = db.cursor()
c.execute('''delete from "exports"''')

def backup_photo(uri,ver=1):
    "Backup the photo, return the new uri"
    if not uri.startswith("file://"): raise ValueError, uri
    oldname=urllib.unquote(uri[7:])
    suffix=uri[uri.rfind('.'):]
    newname=get_new_image_name(oldname,ver)+suffix
    (dirname,filename) = os.path.split(newname)
    if dirname:
        dirname = dirname+"/"
        if os.spawnlp(os.P_WAIT, 'mkdir', 'mkdir', '-p', dirname): raise ValueError, dirname
    basename=os.path.splitext(filename)[0]
    uniquename=basename
    x=1
    while os.spawnlp(os.P_WAIT, 'cp', 'cp', '-l', oldname,
                     os.path.join(dirname,uniquename+suffix)):
        uniquename="%s_%d" % (basename,x)
        x += 1
    return ('file://'+dirname,uniquename+suffix)
c.execute('''select id, base_uri, filename from photos''')
new_photos = [(id, backup_photo(uri+fn)) for id,uri,fn in c]
c.execute('''select photo_id, version_id, base_uri, filename from photo_versions where version_id <> 1''')
new_versions = [(pid, vid, backup_photo(uri+fn,vid)) for pid,vid,uri,fn in c]
for id, (uri, fn) in new_photos:
    c.execute("update photos set base_uri=?, filename=? where id=?",(uri,fn,id))
for id, (uri, fn) in new_photos:
    c.execute("update photo_versions set base_uri=?, filename=? where photo_id=? and version_id=1 ",(uri,fn,id))
for pid, vid, (uri, fn) in new_versions:
    c.execute("update photo_versions set base_uri=?, filename=? where photo_id=? and version_id=? ",(uri,fn,pid,vid))
    

db.commit()
db.close()
