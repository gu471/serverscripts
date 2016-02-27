#add at the bottom of ~/.bashrc

mail -s "ROOTLOGIN@`hostname` from `who | cut -d'(' -f2 | cut -d')' -f1`" admin@mydomain.de << EOF
ALERT - Root Shell Access
on `hostname`:

`date`
`who`
EOF
