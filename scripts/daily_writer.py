import sys
import os
from datetime import datetime

today = datetime.now().year * 10000 + datetime.now().month*100 + datetime.now().day

dtes = []
for line in open('../config/calendar.txt', 'r'):
    p = line.strip().split()
    if len(p) < 6:
        continue

    dte = int(p[0])
    if dte >= today and dte <= today:
        dtes.append(dte)

print dtes

#cmd= 'cd ../bin; \nrm -fr ../log/std.log ../log/err.log;\n'
cmd= 'cd ../bin;\n'
for i in range(0, len(dtes)):
    dte = dtes[len(dtes)-1-i]
    cmd = cmd + 'python hdfwriter.py CF L2 %d >> ../log/std.log 2>>../log/err.log;\n' % (dte)
    cmd = cmd + 'python hdfwriter.py SH L2 %d >> ../log/std.log 2>>../log/err.log;\n' % (dte)
    cmd = cmd + 'python hdfwriter.py SZ L1 %d >> ../log/std.log 2>>../log/err.log;\n' % (dte)
    print cmd
    os.system(cmd);
    
    
    
