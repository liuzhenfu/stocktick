#*-* coding:utf-8 *-*

import email
import mimetypes
from email.MIMEMultipart import  MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEImage import MIMEImage
import smtplib
from hdfconfig import *

def sendEmail(hdfemailinfo,subjectTitle,plainText,htmlText,plainhtmlFlag=1):
    smtpServer = hdfemailinfo.get('smtp')
    emailFrom = hdfemailinfo.get('from')
    emailPwd = hdfemailinfo.get('pwd')
    emailTo = hdfemailinfo.get('to')

    if not (smtpServer and emailFrom and emailPwd and emailTo):
        print 'email info is incomplete.'
        return False

    #set root info
    msgRoot = MIMEMultipart('related')
    subject=str(subjectTitle)
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
    print 'start to send email ....'
    try:
        #print " {0} {1} {2} {3} ".format(smtpServer,emailFrom,emailPwd,emailTo)
        smtp = smtplib.SMTP()
        smtp.connect(smtpServer)
        smtp.login(emailFrom,emailPwd)
        smtp.sendmail(emailFrom,tolist,msgRoot.as_string())
        smtp.quit()
        print 'send success  ...'
        return True
    except :
        print 'send fail ...'
        return False
    return False


if __name__=="__main__":
    hdfemailinfo=gethdfemailinfo()
    subjectTitle=str('hello world test')
    plainText="today is aa 29th 08 2013"
    htmlText="{0}:<br>&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp hello!<br>&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp{1}<br>" \
             "<center><table border='1'>" \
             "<tr><td>111111</td><td>22222</td><td>3333</td></tr></table></center>".format("aaaa"," please see the follow info :")
    sendEmail(hdfemailinfo,subjectTitle,plainText,htmlText)





















