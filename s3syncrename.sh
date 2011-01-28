#! /bin/zsh

# Given a local directory and a remote directory, find the files on
# the remote that exist in the local directory, and if they have a
# different name, issue an 's3cmd mv' call to rename them.
LOCAL=${1?usage $0 local remote}
REMOTE=${2?usage $0 local remote}

( cd "$LOCAL" &&
    md5sum **/* | sort > ../local.txt ) &

s3cmd ls --list-md5 "$REMOTE" | cut -c30- | sort > bucket.txt &

wait

join sbucket.txt slocal.txt | while read md5 FROM TO
do
    s3cmd mv $FROM s3://alan.falloon-backup/photos/$TO
done
