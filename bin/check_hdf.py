# -*- coding: utf-8 -*- #
import sys, os, struct, redis, datetime


dte = datetime.datetime.today().strftime('%Y%m%d')

def process_market_data(head, buf):
    patstr = '<' + 'i'*3 + 'I'*5 + 'I'*10 + 'I'*10 + 'I'*10 + 'I'*10 + 'I' + 'q'*4 + 'I'*2 + 'i'*2 + 'I'*2 + '4s'
    slen = struct.calcsize(patstr)
    N = struct.unpack('<i', buf[0:4])[0]
    for i in range(0, N):
        rv = struct.unpack(patstr, buf[(4+slen*i):(4+slen*(i+1))])
        gid, tme, status, pclse, opn, high, low, lastPx = rv[:8]
        now = datetime.datetime.now()
        tme = str(float(tme)/1e3)
        tme = str(tme.split('.')[0]).zfill(6) + '.' + tme.split('.')[1]
        tme = datetime.datetime.strptime(dte + tme, '%Y%m%d%H%M%S.%f')
        print "current system time: ", now
        print "current tick time: ", tme
        print "delayed seconds: {}s".format((now - tme).total_seconds())
            
def process_index(head, buf):
    patstr = '<i'
    hlen = struct.calcsize(patstr)
    rv = struct.unpack(patstr, buf[0:hlen])
    N = rv[0]
    
    patstr = 'iiiiiiqqi'
    dlen = struct.calcsize(patstr)
    for i in range(N):
        rv = struct.unpack(patstr, buf[(hlen + dlen * i):(hlen + dlen * i + dlen)])
        gid, tme, opn, high, low, lastPx, volume, value, pclse = rv
        now = datetime.datetime.now()
        tme = str(float(tme)/1e3)
        tme = str(tme.split('.')[0]).zfill(6) + '.' + tme.split('.')[1]
        tme = datetime.datetime.strptime(dte + tme, '%Y%m%d%H%M%S.%f')
        print "current system time: ", now
        print "current tick time: ", tme
        print "delayed seconds: {}s".format((now - tme).total_seconds())

r = redis.Redis('192.168.1.16')
ps = r.pubsub()

ps.subscribe('STREAM_HH_RAW_SH_L1')
for msg in ps.listen():
    if msg['type'] != 'message': continue
    head, body = eval(msg['data'])
    if head[1] == 1012:
        process_market_data(head, body)
    elif head[1] == 1113:
        process_index(head, body)
    break

