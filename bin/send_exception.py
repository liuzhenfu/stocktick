# -*- coding: utf-8 -*- #
import sys, os, datetime, glob
from email.MIMEMultipart import  MIMEMultipart
from email.MIMEText import MIMEText
import smtplib


server = 'smtp.qiye.163.com'
user = 'operation@alpha2fund.com'
passwd = 'tms@2016'

def send_email(send_to, subject, content, fmt = 'plain'):
    try:
        COMMASPACE = ', '
        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['To'] = COMMASPACE.join(send_to)
        msg.attach(MIMEText(content, fmt, 'utf-8'))

        smtp = smtplib.SMTP()
        smtp.connect(server)
        smtp.login(user, passwd)
        smtp.sendmail(user, send_to, msg.as_string())
        smtp.close()
        print "send success."
    except Exception, e:
        print "send fail.", e


if __name__ == '__main__':

    dte = int(datetime.datetime.today().strftime('%Y%m%d'))

    tradedays = [int(x[0]) for x in [x.strip().split() for x in open('calendar.txt')] if len(x) == 6]

    if dte not in tradedays:
        print "not trade day, exit."
        sys.exit(-1)

    send_to = ['operation@alpha2fund.com']
    subject = u'TDF数据服务异常-{}'.format(datetime.datetime.now())
    content = open('error.message').read()

    send_email(send_to, subject, content)
