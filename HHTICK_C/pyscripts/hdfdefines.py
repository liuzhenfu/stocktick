#*-* coding:utf-8 *-*
from tables import *
import sys

class market_data(IsDescription):
    dte    = Int32Col()
    tme    = Int32Col()
    pclse  = Int32Col()
    opn    = Int32Col()
    high   = Int32Col()
    low    = Int32Col()
    lastPx = Int32Col()
    tcount = Int32Col()
    volume = Int64Col()
    value  = Int64Col()
    
    ask1   = Int32Col()
    ask2   = Int32Col()
    ask3   = Int32Col()
    ask4   = Int32Col()
    ask5   = Int32Col()
    ask6   = Int32Col()
    ask7   = Int32Col()
    ask8   = Int32Col()
    ask9   = Int32Col()
    ask10  = Int32Col()

    asize1   = Int32Col()
    asize2   = Int32Col()
    asize3   = Int32Col()
    asize4   = Int32Col()
    asize5   = Int32Col()
    asize6   = Int32Col()
    asize7   = Int32Col()
    asize8   = Int32Col()
    asize9   = Int32Col()
    asize10  = Int32Col()

    bid1   = Int32Col()
    bid2   = Int32Col()
    bid3   = Int32Col()
    bid4   = Int32Col()
    bid5   = Int32Col()
    bid6   = Int32Col()
    bid7   = Int32Col()
    bid8   = Int32Col()
    bid9   = Int32Col()
    bid10  = Int32Col()

    bsize1   = Int32Col()
    bsize2   = Int32Col()
    bsize3   = Int32Col()
    bsize4   = Int32Col()
    bsize5   = Int32Col()
    bsize6   = Int32Col()
    bsize7   = Int32Col()
    bsize8   = Int32Col()
    bsize9   = Int32Col()
    bsize10  = Int32Col()
    
class transaction(IsDescription):
    dte    = Int32Col()
    tme    = Int32Col()
    idx    = Int32Col()
    prc    = Int32Col()
    qty    = Int32Col()
    val    = Int32Col()

class market_index(IsDescription):
    dte    = Int32Col()
    tme    = Int32Col()
    pclse  = Int32Col()
    opn    = Int32Col()
    high   = Int32Col()
    low    = Int32Col()
    lastPx = Int32Col()
    volume = Int64Col()
    value  = Int64Col()
    
class market_data_futures(IsDescription):
    dte    = Int32Col()
    tme    = Int32Col()
    pclse  = Int32Col()
    popi   = Int32Col()
    psettle= Int32Col()
    opn    = Int32Col()
    high   = Int32Col()
    low    = Int32Col()
    lastPx = Int32Col()
    opi    = Int32Col()
    settle = Int32Col()
    volume = Int64Col()
    value  = Int64Col()
    
    ask1   = Int32Col()
    ask2   = Int32Col()
    ask3   = Int32Col()
    ask4   = Int32Col()
    ask5   = Int32Col()

    asize1   = Int32Col()
    asize2   = Int32Col()
    asize3   = Int32Col()
    asize4   = Int32Col()
    asize5   = Int32Col()

    bid1   = Int32Col()
    bid2   = Int32Col()
    bid3   = Int32Col()
    bid4   = Int32Col()
    bid5   = Int32Col()

    bsize1   = Int32Col()
    bsize2   = Int32Col()
    bsize3   = Int32Col()
    bsize4   = Int32Col()
    bsize5   = Int32Col()

class market_data_L1(IsDescription):
    dte    = Int32Col()
    tme    = Int32Col()
    pclse  = Int32Col()
    opn    = Int32Col()
    high   = Int32Col()
    low    = Int32Col()
    lastPx = Int32Col()
    volume = Int64Col()
    value  = Int64Col()

    ask1   = Int32Col()
    ask2   = Int32Col()
    ask3   = Int32Col()
    ask4   = Int32Col()
    ask5   = Int32Col()

    asize1   = Int32Col()
    asize2   = Int32Col()
    asize3   = Int32Col()
    asize4   = Int32Col()
    asize5   = Int32Col()

    bid1   = Int32Col()
    bid2   = Int32Col()
    bid3   = Int32Col()
    bid4   = Int32Col()
    bid5   = Int32Col()

    bsize1   = Int32Col()
    bsize2   = Int32Col()
    bsize3   = Int32Col()
    bsize4   = Int32Col()
    bsize5   = Int32Col()

class market_data_futures_L1(IsDescription):
    dte    = Int32Col()
    tme    = Int32Col()
    pclse  = Int32Col()
    popi   = Int32Col()
    psettle= Int32Col()
    opn    = Int32Col()
    high   = Int32Col()
    low    = Int32Col()
    lastPx = Int32Col()
    opi    = Int32Col()
    settle = Int32Col()
    volume = Int64Col()
    value  = Int64Col()

    ask1   = Int32Col()
    asize1   = Int32Col()
    bid1   = Int32Col()
    bsize1   = Int32Col()

class emailMsg:
    _paramErrorTitle = "Error(14):start to get market data Error"
    _paramErrorContent = "the usage info error,not give 4 parameter usage: filename SH/SZ/CF L2/L1 dte."

    _loginErrorTitle = "Error(14):Login On HH Server Error."
    _loginErrorContent = "LogError,Get {0}_{1}_{2} Market Data Error.user {3} log error.ip:{4},port:{5},please check the user or hhserver."

    _configErrorTitle = "Error(14): Config file Error"
    _configErrorContent = "The config file is not supply the complete info of the hhserver ,please check the cfg file."

    _timeoutErrorTitle="Error(14):{0}_{1}_{2} timeout Error"
    _timeoutErrorContent="Get {0}_{1}_{2} markt data Error.Recv hh response timeout,set timeout time is :{3}s "

    _getDataErrorTitle="Error(14):{0}_{1}_{2} get market data Error"
    _getDataErrorContent="Get {0}_{1}_{2} markt data Error:{3}. "

    _systemOnExitErrorTitle="Error(14):{0}_{1}_{2} ,system On Exit"
    _systemOnExitErrorContent="Get {0}_{1}_{2} ,system time On Exit,pls check the org data "

    _getMarketDataSuccessTitle = "Success(14):Get {0}_{1}_{2} Market Data Success"
    _getMarketDataSuccessContent = "Get {0}_{1}_{2} finish.<br>Detail info:<br>Market_Data cnt:{3} &nbsp&nbsp&nbsp&nbsp;Transaction cnt:{4} &nbsp&nbsp&nbsp&nbsp;Index cnt:{5} &nbsp&nbsp&nbsp&nbsp;CF_Market_Data_futures cnt {6} ;"

    _getMarketDataExceptionTitle = "Exception(14):Get {0}_{1}_{2} Market Data Exception"
    

    _checkHtmlPre = '''<HTML><HEAD><title>checkresult</title><META HTTP-EQUIV='content-type' CONTENT='text/html; charset=utf-8'>''' \
                    '''<style type=text/css> td{font-size:9pt;border:solid 1 #000000;}table{padding:3 0 3 0;border:solid 1 #000000;margin:0 0 0 0;BORDER-COLLAPSE: collapse;} </style>'''

    _checkHtmlLast= "</HEAD><BODY>{0}<BR><P>If in doubt, please view the logs or contact the relevant personnel,ths</P></BODY></HTML>"
                           
    
    _checkMarketDataL2Content = "<BR><P>MarketData_CheckResult：</P>"
    _checkMarketDataL2Table = "<BR><table cellSpacing='0' cellPadding='0' width ='100%' border='1'><tr><td width='6%'>dte</td><td width='6%'>tkr</td><td width='6%'>cnt</td><td width='6%'>begintme</td><td width='6%'>lasttme</td>" \
                           "<td width='7%'>avgasize1</td><td width='7%'>avgasize2</td><td width='7%'>avgasize3</td><td width='7%'>avgasize4</td><td width='7%'>avgasize5</td><td width='7%'>avgbsize1</td><td width='7%'>avgbsize2</td><td width='7%'>avgbsize3</td>" \
                           "<td width='7%'>avgbsize4</td><td width='7%'>avgbsize5</td></tr>{0}</table>"
    _checkMarketDataL2Td = "<tr><td>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}</td><td>{5}</td><td>{6}</td><td>{7}</td><td>{8}</td><td>{9}</td><td>{10}</td><td>{11}</td><td>{12}</td><td>{13}</td><td>{14}</td></tr>"

    _checkTransactionContent = "<BR><P>Transaction_CheckResult：</P>"
    _checkTransactionTable = "<BR><table cellSpacing='0' cellPadding='0' width ='100%' border='1'><tr><td width='16%'>dte</td><td width='16%'>tkr</td><td width='16%'>cnt</td><td width='16%'>begintme</td><td width='16%'>lasttme</td>" \
                           "<td width='20%'>avgVolume</td></tr>{0}</table>"
    _checkTransactionTd = "<tr><td>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}</td><td>{5}</td></tr>"

    _checkIndexContent = "<BR><P>Index_CheckResult：</P>"
    _checkIndexTable = "<BR><table cellSpacing='0' cellPadding='0' width ='100%' border='1'><tr><td width='16%'>dte</td><td width='16%'>tkr</td><td width='16%'>cnt</td><td width='16%'>begintme</td><td width='16%'>lasttme</td>" \
                           "<td width='20%'>avgVolume</td></tr>{0}</table>"
    _checkIndexTd = "<tr><td>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}</td><td>{5}</td></tr>"

    _checkCFL2Content = "<BR><P><BR>CF_MarketData_Future_CheckResult：：</P>"
    _checkCFL2Table = "<BR><table cellSpacing='0' cellPadding='0' width ='100%' border='1'><tr><td width='6%'>dte</td><td width='6%'>tkr</td><td width='6%'>cnt</td><td width='6%'>begintme</td><td width='6%'>lasttme</td>" \
                           "<td width='7%'>avgasize1</td><td width='7%'>avgasize2</td><td width='7%'>avgasize3</td><td width='7%'>avgasize4</td><td width='7%'>avgasize5</td><td width='7%'>avgbsize1</td><td width='7%'>avgbsize2</td><td width='7%'>avgbsize3</td>" \
                           "<td width='7%'>avgbsize4</td><td width='7%'>avgbsize5</td></tr>{0}</table>"
    _checkCFL2Td = "<tr><td>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}</td><td>{5}</td><td>{6}</td><td>{7}</td><td>{8}</td><td>{9}</td><td>{10}</td><td>{11}</td><td>{12}</td><td>{13}</td><td>{14}</td></tr>"

    _checkCFL1Content = "<BR><P><BR>CF_MarketData_Future_CheckResult：</P>"
    _checkCFL1Table = "<BR><table cellSpacing='0' cellPadding='0' width ='100%' border='1'><tr><td width='14%'>dte</td><td width='14%'>tkr</td><td width='14%'>cnt</td><td width='14%'>begintme</td><td width='14%'>lasttme</td>" \
                           "<td width='15%'>avgasize1</td><td width='15%'>avgbsize1</td></tr>{0}</table>"
    _checkCFL1Td = "<tr><td>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}</td><td>{5}</td><td>{6}</td></tr>"
