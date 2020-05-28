import sys
import os

dtes = []
for line in open('../config/calendar.txt', 'r'):
    p = line.strip().split()
    if len(p) < 6:
        continue

    dte = int(p[0])
    if dte < 20130827 or dte >= 20130903:
        continue

    dtes.append(dte)

print dtes

fp = open('savehdf.sh', 'w')

print >>fp, 'cd ../bin; rm -fr ../log/std.log ../log/err.log'
for i in range(0, len(dtes)):
    dte = dtes[len(dtes)-1-i]
    cmd = 'python hdfwriter.py SH L2 %d >> ../log/std.log 2>>../log/err.log' % (dte)
    print >>fp, cmd
    
    
    
