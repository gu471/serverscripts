#!/bin/bash
export HOME=/var/spool/amavisd/.spamassassin/
cd /tmp
mkdir /tmp/tmpspam
mkdir /tmp/tmpham

echo "starting sa-learn-script"

for SPAMDIR in $(find /var/spool/imap/ -type d -wholename "*Spam/spam*")
do
  echo "  for" $SPAMDIR
  cp -r $SPAMDIR/* /tmp/tmpspam
  chown amavis /tmp/tmpspam/*
  su -c "sa-learn --dbpath $HOME --spam /tmp/tmpspam/[0-9]*" - amavis
  rm -r /tmp/tmpspam/*
done

rmdir /tmp/tmpspam

for HAMDIR in $(find /var/spool/imap/ -type d -wholename "*Spam/ham*")
do
  echo "  for" $HAMDIR
  cp -r $HAMDIR/* /tmp/tmpham
  chown amavis /tmp/tmpham/*
  sa-learn --dbpath $HOME --ham /tmp/tmpham/[0-9]*
  rm -r /tmp/tmpham/*
done

rmdir /tmp/tmpham

su -c "sa-learn --sync" - amavis

echo "    deleting files older than 7 days in SPAM"
/usr/lib/cyrus-imapd/ipurge -f -d 7 user/*/Spam/spam@gu471.de
echo "    deleting files older than 14 days in HAM"
/usr/lib/cyrus-imapd/ipurge -f -d 14 user/*/Spam/ham@gu471.de
