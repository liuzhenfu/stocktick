#*-* coding:gbk *-*
import sys

import ConfigParser

import logging

def getLogHandler(modelName,logName = "../log/loghdf.log"):
    logFMT=logging.Formatter("%(name)s : %(levelname)s %(process)d %(asctime)s {%(message)s}")
    logger=logging.getLogger(modelName)
    handler = logging.FileHandler(logName)
    handler.setFormatter(logFMT)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    def gethandler():
        return logger
    return gethandler()

cpath = '../config/hdf5cfg.ini'

def gethhserverinfo(hhlevel = "L2"):
    cfile=open(cpath,'r')
    config=ConfigParser.ConfigParser()
    config.readfp(cfile)
    hhserverinfo = {}
    hhserver = "hhserverL2"
    if hhlevel.upper() == "L1":
        hhserver = "hhserverL1"
    hhserverinfo['ip'] = config.get(hhserver,"ip")
    hhserverinfo['port'] = int(config.get(hhserver,"port"))
    hhserverinfo['user'] = config.get(hhserver,"user")
    hhserverinfo['pwd'] = config.get(hhserver,"pwd")
    cfile.close()
    return hhserverinfo

def gethdfemailinfo():
    hdfemailinfo = {}
    cfile=open(cpath,'r')
    config=ConfigParser.ConfigParser()
    config.readfp(cfile)
    hdfemailinfo['smtp'] = config.get("hdfEmail","smtp")
    hdfemailinfo['from'] = config.get("hdfEmail","from")
    hdfemailinfo['pwd'] = config.get("hdfEmail","pwd")
    hdfemailinfo['to'] = config.get("hdfEmail","to")
    cfile.close()
    return hdfemailinfo

def gethdfdbpathinfo():
    hdfdbpathinfo = {}
    cfile=open(cpath,'r')
    config=ConfigParser.ConfigParser()
    config.readfp(cfile)
    hdfdbpathinfo['SH_L2'] = config.get("hdf5db","SH_L2")
    hdfdbpathinfo['SH_L1'] = config.get("hdf5db","SH_L1")
    hdfdbpathinfo['SZ_L2'] = config.get("hdf5db","SZ_L2")
    hdfdbpathinfo['SZ_L1'] = config.get("hdf5db","SZ_L1")
    hdfdbpathinfo['CF_L2'] = config.get("hdf5db","CF_L2")
    hdfdbpathinfo['CF_L1'] = config.get("hdf5db","CF_L2")
    cfile.close()
    return hdfdbpathinfo

def getcheckfilepathinfo():
    checkfilepathinfo = {}
    cfile=open(cpath,'r')
    config=ConfigParser.ConfigParser()
    config.readfp(cfile)
    checkfilepathinfo['SH_CHECK_TKR'] = config.get("checkfile","SH_CHECK_TKR")
    checkfilepathinfo['SZ_CHECK_TKR'] = config.get("checkfile","SZ_CHECK_TKR")
    checkfilepathinfo['CF_CHECK_TKR'] = config.get("checkfile","CF_CHECK_TKR")
    checkfilepathinfo['SH_CHECK_INDEX'] = config.get("checkfile","SH_CHECK_INDEX")
    checkfilepathinfo['SZ_CHECK_INDEX'] = config.get("checkfile","SZ_CHECK_INDEX")
    cfile.close()
    return checkfilepathinfo


if __name__ == '__main__':
    hhserverinfo=gethhserverinfo()
    print ' ip:',hhserverinfo.get('ip'),' port:',hhserverinfo.get('port'),' user:',hhserverinfo.get('user'),' pwd:',hhserverinfo.get('pwd')

    hdfemailinfo=gethdfemailinfo()
    print 'smtp:',hdfemailinfo.get('smtp'),' emailFrom:',hdfemailinfo.get('from'),' passwd:',hdfemailinfo.get('pwd'),' emailTo:',hdfemailinfo.get('to')

    hdfdbpathinfo=gethdfdbpathinfo()
    print 'ssSH_L2:{0} SH_L1:{1} SZ_L2:{2} SZ_L1:{3}'.format(hdfdbpathinfo.get('SH_L2'),hdfdbpathinfo['SH_L1'],hdfdbpathinfo['SZ_L2'],hdfdbpathinfo['SZ_L1'])









