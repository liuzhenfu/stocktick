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
    if dte >= 20140501 and dte <= 20140513:
        dtes.append(dte)
#dtes =[20130329,20130401,20130517,20130701,20140218]
#print dtes
#cmd= 'cd ../bin; \nrm -fr ../log/std.log ../log/err.log;\n'
cmd= 'cd ../bin;\n'
for i in range(0, len(dtes)):
    dte = dtes[len(dtes)-1-i]
    #cmdcf = cmd + 'python hdfwriter.py CF L2 %d >> ../log/std.log 2>>../log/err.log;\n' % (dte)
    #cmdcf = cmd + 'python hdfwriter.py CF L2 %d \n' % (dte)
    #print cmdcf
    #os.system(cmdcf)
    #cmdsh = cmd + 'python hdfwriter.py SH L2 %d >> ../log/std.log 2>>../log/err.log;\n' % (dte)
    cmdsh = cmd + 'python hdfwriter.py SH L2 %d \n' % (dte)
    os.system(cmdsh)
    print cmdsh
    #cmdsz = cmd + 'python hdfwriter.py SZ L1 %d >> ../log/std.log 2>>../log/err.log;\n' % (dte)
    #cmdsz = cmd + 'python hdfwriter.py SZ L1 %d \n' % (dte)
    #print cmdsz
    #os.system(cmdsz);
    
    
    
