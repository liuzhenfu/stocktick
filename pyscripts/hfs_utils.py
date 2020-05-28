#coding:gbk
from common.hfs_config import *
import sys,select,time,ConfigParser,redis,re,datetime,pdb
import email
import mimetypes
from email.header import Header
from email.MIMEMultipart import  MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEImage import MIMEImage
import smtplib
from collections import defaultdict

def strstrip(ss):
    return ss[0:ss.find('\0')]

def readconfig(fname):
    cfile=open(fname,'r')
    config=ConfigParser.ConfigParser()
    config.readfp(cfile)
    cfile.close()
    return config

config = readconfig(hfs_config.config_path)
################################ TIME UTILS ###########################################

def hhmmssmss_to_mss(hhmmssmss):
    hhmmss = hhmmssmss / 1000
    return hhmmss_to_s(hhmmss) * 1000 + hhmmssmss % 1000

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
    if tidx < 0:
        return -1
    elif tidx < 135 * 60:
        return tidx
    elif tidx < 135 * 60 + 90 * 60:
        return 135 * 60
    elif tidx < 135 * 60 + 90 * 60 + 135 * 60:
        return tidx - 90 * 60
    else:
        return -2

def extend_time_to_hhmmss(tidx): #按照期货交易时间进行计算
    if tidx >= 135 * 60: tidx+= 90 * 60
    return s_to_hhmmss(hhmmss_to_s(91500) + tidx)

def today(): # return today datestring, format: 2011-01-05
    return time.strftime('%Y-%m-%d', time.localtime())

####################### DATABASE ###################################
def get_redis_conn(myhost=None,port=None,passwd=None,db=None):
    if not myhost:
        redis_host   = config.get('redis','host')
        redis_port   = config.get('redis','port')
        redis_passwd = config.get('redis','passwd')
        r = redis.Redis(host=redis_host,port=int(redis_port),password=redis_passwd,db=0)
    else:
        r = redis.Redis(host=myhost, port=port or 6379, password=passwd or '', db=db or 0)
    return r

def get_oracle_conn(oracle_host=None,oracle_port=None,oracle_user=None,oracle_passwd=None,oracle_sid=None):
    import cx_Oracle
    if not oracle_host:
        oracle_host   = config.get('oracle','host')
        oracle_port   = config.get('oracle','port')
        oracle_user   = config.get('oracle','user')
        oracle_passwd = config.get('oracle','passwd')
        oracle_sid    = config.get('oracle','sid')

        conn = cx_Oracle.connect(oracle_user,oracle_passwd,'%s:%s/%s'%(oracle_host,oracle_port,oracle_sid))
    else:
        conn = cx_Oracle.connect(oracle_user,oracle_passwd,'%s:%s/%s'%(oracle_host,oracle_port,oracle_sid))
    return conn

def get_mongo_conn():
    import pymongo
    mongo = pymongo.MongoClient('localhost',27017)
    return mongo

def set_db_name(runmode):
    if runmode == 'backtest':
        hfs_config.db_name = 'ftrade_backtest'
    elif runmode == 'simulation':
        hfs_config.db_name = 'ftrade_simulation'
    elif runmode == 'online':
        hfs_config.db_name = 'ftrade_online'
    else:
        raise Exception('')
    print >>sys.stderr, 'set_db_name:', hfs_config.db_name


####################### EMAIL ######################################
def send_report(title, body):
    r = get_redis_conn()
    r.publish('pyhfs_report', { 'title':title, 'body':body })

def sendEmail(subjectTitle, plainText, htmlText='', plainhtmlFlag = 1):
    '''
    sending alert message through email, short msg or phone call
    '''
    config     = readconfig(hfs_config.config_path)
    smtpServer = config.get("Email","smtp")
    emailFrom  = config.get("Email","from")
    emailPwd   = config.get("Email","pwd")
    emailTo    = config.get("Email","to")

    #set root info
    msgRoot = MIMEMultipart('related')
    #subject = str(subjectTitle)
    subject = Header(subjectTitle,'utf-8')
    msgRoot['Subject'] = subject #??
    msgRoot['From'] = emailFrom
    tolist=emailTo.split(',')
    msgRoot['To'] = emailTo

    #msgRoot.preamble = 'This is a multi-part message in MiME format.' #??

    #Encapsulate the plain and HTML versions of the message body in an
    #'alternative' part, so message agents can decide which they want to display.
    msgAlternative = MIMEMultipart('alternative')
    msgRoot.attach(msgAlternative)

    if plainhtmlFlag == 1:
        #set msgText info
        msgText = MIMEText(plainText,'plain','utf-8')
        msgAlternative.attach(msgText)
    else:
        #set HTML info
        msgHTML=MIMEText(htmlText,'html','utf-8')
        msgAlternative.attach(msgHTML)

    #send email
    smtp = None
    print >>sys.stderr, 'start to send email ....'
    try:
        #print " {0} {1} {2} {3} ".format(smtpServer,emailFrom,emailPwd,emailTo)
        smtp = smtplib.SMTP()
        smtp.connect(smtpServer)
        #smtp = smtplib.SMTP('localhost')
        smtp.login(emailFrom,emailPwd)
        smtp.sendmail(emailFrom,tolist,msgRoot.as_string())
        smtp.quit()
        print >>sys.stderr, 'send success  ...'
        return True
    except :
        print >>sys.stderr, 'send fail ...'
        return False
    return False

calendar = config.get('trade_engine', 'Calendar')
with open(calendar,'r') as f:
    res = [x.strip().split() for x in f.readlines()]
    alldays = [int(x[0]) for x in res]
    tradedays = [int(x[0]) for x in res if len(x)==6]

# get the previous trade day
def prev_dte(dte, cnt=1):
    ndte = [x for x in tradedays if x<dte]
    return ndte[-cnt]

# get the next trade day
def next_dte(dte):
    ndte = [x for x in tradedays if x>dte]
    return ndte[0]

# get days list:
def range_dte(dte1,dte2):
    ndte = [x for x in alldays if x>=dte1 and x <=dte2]
    return ndte

# check whether trading day
def is_tradeday(dte):
    return dte in tradedays

# convert tkr to wind format
def windy_tkr(tkr,dtype):
    dtype = dtype.upper()
    if dtype == 'S': # Stock
        ntkr = str(tkr).zfill(6)
        if ntkr[0] == '6' or ntkr[0] == '5' or ntkr[0] == '7':
            return u'%s.SH'%ntkr
        elif ntkr[0] == '0' or ntkr[0] == '1' or ntkr[0] == '3':
            return u'%s.SZ'%ntkr
        else:
            return u'%s.UK'%ntkr #unknown
    elif dtype == 'F': # Future
        ntkr = tkr.upper()
        res  = re.findall('(^\D+)[0-9]+', ntkr)
        if res != []:
            abbr = res[0]
            if abbr in ['IC','IF','IH','T','TF']:
                return u'%s.CFE'%ntkr
            elif abbr in ['AG','AL','AU','BU','CU','FU','HC','NI','PB','RB','RU','SN','WR','ZN']:
                return u'%s.SHF'%ntkr
            elif abbr in ['CF','FG','JR','LR','ME','MA','OI','PM','WT','WS','RO','RI','ER','RM','RS','SF','SM','SR','TA','TC','WH','ZC']:
                return u'%s.CZC'%ntkr
            elif abbr in ['A','M','Y','P','C','I','JM','J','L','V','B','JD','FB','BB','PP','CS']:
                return u'%s.DCE'%ntkr
            else:
                return u'%s.UKF'%ntkr
        else:
            return u'%s.UKF'%ntkr #unknown future
    else:
        raise Exception('windy_tkr error: Unknown Type: %r'%dtype)

def is_com_tradetme(tme):
    return (tme>=90000 and tme<101500) or (tme>=103000 and tme<113000) or (tme>=133000 and tme<150000) or (tme>=0 and tme<23000) or (tme>=210000 and tme<240000)

def get_ctamin(cycle=1):
    start  = datetime.datetime(2016,1,1,0,0,0)
    end    = datetime.datetime(2016,1,1,23,59,59)
    step   = datetime.timedelta(0,60)
    series = [int(x.strftime('%H%M00')) for x in gen_date_series(start,end,step)]
    ctamin = [x for x in series if x/100%cycle==0 and is_com_tradetme(x)]
    return ctamin

def gen_date_series(start,end,step):
    result = []
    while start <= end:
        result.append(start)
        start += step
    return result

timescheme_path = config.get('trade_engine','TimeScheme')
timescheme = defaultdict(list)
with open(timescheme_path,'r') as f:
    for line in f:
        tkrtype,dte,scheme = line.strip().split()
        timescheme[tkrtype].append([int(dte),eval(scheme.replace(';',','))])

def is_tradetme(tkr,dte,tme):
    res  = re.findall('(^\D+)[0-9]*', tkr.upper())
    if not res:
        raise Exception('invalid tkr ',tkr)
    tkrtype = res[0]
    scheme  = timescheme.get(tkrtype)
    if not scheme:
        raise Exception('unknown tkrtype')
    idx = [i for i,x in enumerate(scheme) if dte<=x[0]][0]
    tradetme = scheme[idx][1]
    for t in tradetme:
        if tme==240000:
            return False
        if tme==0 and t[0]==0:
            return True
        if tme>t[0] and tme<=t[1]:
            return True
    return False

def parse_tkrs(dte, tkrs):
    conn = get_oracle_conn()
    cursor = conn.cursor()
    sql = "SELECT orgsecucode FROM PRODRW.COMMODITYFUTURESBASEINFO WHERE startdate<="+str(dte)+" AND enddate>="+str(dte)+" AND secutype='%s' ORDER BY secucode"
    result = []
    for tkr in tkrs:
        abbr = re.findall('(^\D+)[0-9]+',tkr)[0]
        code = int(re.findall('^\D+([0-9]+)',tkr)[0])
        res  = cursor.execute(sql%abbr).fetchall()[code-1][0]
        result.append(res)
    return result
