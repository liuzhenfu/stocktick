#coding:gbk
import select #set timeout
import sys

def loop_recv_old(s, nlen):
    ''' 网络通信时，接收指定长度的字节流 '''
    n = 0
    to_recv = nlen
    rv = ''
    while True:
        buf = s.recv(to_recv)
        rv+= buf
        to_recv-= len(buf)
        if to_recv == 0: break
    return rv

def loop_recv(s, nlen):
    rv=loop_recv_usetimeount(s, nlen,5)
    return rv

def loop_recv_usetimeount(s, nlen,timeout=5):
    ''' 网络通信时，接收指定长度的字节流 '''
    n = 0
    to_recv = nlen
    rv = ''
    while True:
        recvtimeout=select.select([s],[],[],timeout)
        if recvtimeout[0] == []:
            print 'recv hh response timeout,set timeout time is : ',timeout
            sys.exit(-1)
        #else :
            #print 'recv hh respone ok.'
        
        buf = s.recv(to_recv)
        rv+= buf
        to_recv-= len(buf)
        if to_recv == 0: break
    return rv
    
def strstrip(ss):
    return ss[0:ss.find('\0')]

def hhmmss_to_s(hhmmss):
    return hhmmss/10000 * 3600 + (hhmmss/100 % 100) * 60 + hhmmss % 100

def s_to_hhmmss(s):
    return s/3600 * 10000 + s % 3600 / 60 * 100 + s % 60

def normal_time_to_hhmmss(ss):
    if ss < 0:
        return -1
    elif ss < 120*60:
        return s_to_hhmmss(hhmmss_to_s(93000) + ss)
    else:
        return s_to_hhmmss(hhmmss_to_s(93000) + 90*60 + ss)

def hhmmss_to_normal_time(hhmmss):
    ss = hhmmss_to_s(hhmmss) - hhmmss_to_s(93000)
    if ss < 0:
        return -1
    elif ss < 120 * 60:
        return ss
    elif ss < 120 * 60 + 90 * 60:
        return 120 * 60
    elif ss < 120 * 60 + 90 * 60 + 120 * 60:
        return ss - 90 * 60
    else:
        return -2

def tme_to_idx(hhmmss): #找到对应的分钟数
    ntime = hhmmss_to_normal_time(hhmmss)
    if ntime < 0: return -1
    return ntime / 60

def idx_to_tme(idx): #分钟=>时间
    return normal_time_to_hhmmss(idx * 60)

def hhmmss_to_extend_time(tme): #按照期货交易时间进行计算
    tidx = hhmmss_to_s(tme) - hhmmss_to_s(91500)
    if tidx < 0: return -1
    if tidx >= 135 * 60: tidx-= 90 * 60
    if tidx >= 270 * 60: return -2
    return tidx

def extend_time_to_hhmmss(tidx): #按照期货交易时间进行计算
    if tidx >= 135 * 60: tidx+= 90 * 60
    return s_to_hhmmss(hhmmss_to_s(91500) + tidx)

def today(): # return today datestring, format: 2011-01-05
    import time
    return time.strftime('%Y-%m-%d', time.localtime())
