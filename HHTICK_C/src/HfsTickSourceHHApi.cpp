#include "HfsTickSourceHHApi.hpp" 
#include "HfsLog.hpp"
#include <string>
#include <unistd.h>
#include <functional>
#include <iostream>
#include <sstream>
#include "xml_parser.hpp"

using namespace std;
HfsTickSourceHHApi::HfsTickSourceHHApi( ) {
    reading_ = false;
    multi_cons_ = false;
    // loadConfig(configFile);
}

HfsTickSourceHHApi::~HfsTickSourceHHApi() {
    fclose(pFile_);
}

bool HfsTickSourceHHApi::loadConfig(const char* configFile) {
    a2ftool::XmlNode root_node(configFile);
    a2ftool::XmlNode HH_node = root_node.getChild("HHL2");
    address_ = HH_node.getAttrDefault("HHL2Address", "172.18.100.162");
    port_ = HH_node.getAttrDefault("HHL2Port", "20002");
    user_ = HH_node.getAttrDefault("HHL2User", "alpha2fund");
    passwd_ = HH_node.getAttrDefault("HHL2Passwd", "alph1234");
    address_bak_ = HH_node.getAttrDefault("HHL2Address_bak", "172.18.100.150");
    port_bak_ = HH_node.getAttrDefault("HHL2Port_bak", "20002");
    cout << "address : " << address_
         << "\nport : " << port_
         << "\nusr : " << user_
         << "\naddress_bak : " << address_bak_ 
         << "\nport_bak : " << port_bak_
         << endl;

    sprintf(filename_, "../data/HHTICK_%d.txt", dte_);
    cout << filename_ << endl;
    pFile_ = fopen(filename_, "a+");
    if (!pFile_){
        cout << "open file failed" << endl;
        return false;
    }
    return true;
}

bool HfsTickSourceHHApi::login() {
    TDF_ERR nErr = TDF_ERR_SUCCESS;
    THANDLE hTDF = NULL;
    TDF_SetEnv(TDF_ENVIRON_OUT_LOG, 1);
    if (multi_cons_) {
        TDF_OPEN_SETTING_EXT settings = {0};
        memset(&settings, 0, sizeof(settings));
        strncpy(settings.siServer[0].szIp, address_.c_str(), sizeof(settings.siServer[0].szIp) - 1);
        strncpy(settings.siServer[0].szPort, port_.c_str(), sizeof(settings.siServer[0].szPort) - 1);
        strncpy(settings.siServer[0].szUser, user_.c_str(), sizeof(settings.siServer[0].szUser) - 1);
        strncpy(settings.siServer[0].szPwd, passwd_.c_str(), sizeof(settings.siServer[0].szPwd) - 1);

        strncpy(settings.siServer[0].szIp, address_bak_.c_str(), sizeof(settings.siServer[0].szIp) - 1);
        strncpy(settings.siServer[0].szPort, port_bak_.c_str(), sizeof(settings.siServer[0].szPort) - 1);
        strncpy(settings.siServer[0].szUser, user_.c_str(), sizeof(settings.siServer[0].szUser) - 1);
        strncpy(settings.siServer[0].szPwd, passwd_.c_str(), sizeof(settings.siServer[0].szPwd) - 1);

        // settings.nServerNum = 2;              //必须设置： 有效的连接配置个数（当前版本应<=2)
        settings.pfnMsgHandler = on_recv_data; //设置数据消息回调函数
        settings.pfnSysMsgNotify = on_recv_sys; //设置系统消息回调函数
        settings.szMarkets = "SH-2-0;SZ-2-0"; //需要订阅的市场列表 SZ-L2-股票/期权

        settings.szSubScriptions = ""; //"600030.SH"; //600030.SH;104174.SH;103493.SH";    //需要订阅的股票,为空则订阅全市场
        settings.nTime = 0xffffffff;   //请求的时间，格式HHMMSS，为0则请求实时行情，为0xffffffff从头请求
        settings.nTypeFlags = DATA_TYPE_ALL; // 数据类型订阅！支持订阅3种类型TRANSACTION;ORDER;ORDERQUEUE。 ！注意：行情数据任何时候都发送，不需要订阅! 参见enum DATA_TYPE_FLAG

        hTDF = TDF_OpenExt(&settings, &nErr);
    } else {
        TDF_OPEN_SETTING settings = {0};
        memset(&settings, 0, sizeof(settings));
        strncpy(settings.szIp, address_.c_str(), sizeof(settings.szIp) - 1);
        strncpy(settings.szPort, port_.c_str(), sizeof(settings.szPort) - 1);
        strncpy(settings.szUser, user_.c_str(), sizeof(settings.szUser) - 1);
        strncpy(settings.szPwd, passwd_.c_str(), sizeof(settings.szPwd) - 1);

        settings.pfnMsgHandler = on_recv_data; //设置数据消息回调函数
        settings.pfnSysMsgNotify = on_recv_sys; //设置系统消息回调函数
        settings.szMarkets = "SZ;SH"; //需要订阅的市场列表

        settings.szSubScriptions = ""; //"600030.SH"; //600030.SH;104174.SH;103493.SH";    //需要订阅的股票,为空则订阅全市场
        settings.nTime = 0xffffffff;            //请求的时间，格式HHMMSS，为0则请求实时行情，为0xffffffff从头请求
        settings.nTypeFlags = DATA_TYPE_ALL;

        hTDF = TDF_Open(&settings, &nErr);
    }
    if (hTDF == NULL) {
        FLOG << "TDF_OPEN return error: " << nErr;
    } else {
        reading_ = true;
        TLOG << "TDF_OPEN success!";
    }
    return reading_;
}

bool HfsTickSourceHHApi::on_bmo() {
    return login();
}

bool HfsTickSourceHHApi::on_amc() {
    return true;
}

bool HfsTickSourceHHApi::run() {
    while(reading_) {
        sleep(1);
    }
    return true;
}

int HfsTickSourceHHApi::process_code_table(TDF_CODE *pCodeTable, unsigned int cnt){
    printf("-------- code table, Count:%d --------\n", cnt);
    return 0;
}

int HfsTickSourceHHApi::process_market_data(TDF_MARKET_DATA* pMarket, unsigned int cnt) {
    cout << "recv mkt data" << endl;
    printf("-------- Market, Count:%d --------\n", cnt);
    for (unsigned int i = 0; i < cnt;++i){
        const TDF_MARKET_DATA &marketData = pMarket[i];
        stringstream ss;
        ss << "market data: "
           << " tkr: " << marketData.szWindCode
           << " tme: " << marketData.nTime
           << " lastPrc: " << marketData.nMatch
           << " ask1: " << marketData.nAskPrice[0]
           << " askv1: " << marketData.nAskVol[0]
           << " bid1: " << marketData.nBidPrice[0]
           << " bidv1: " << marketData.nBidVol[0]
           << " shr: " << marketData.iVolume
           << " val: " << marketData.iTurnover
           << " endl\n";
        fwrite(ss.str().c_str(), sizeof(char), ss.str().length(), pFile_ );
    }
    return 0;
}
int HfsTickSourceHHApi::process_index_data(TDF_INDEX_DATA *pIndex, unsigned int cnt) {
    for (unsigned int i = 0; i < cnt; ++i){
        const TDF_INDEX_DATA &indexData = pIndex[i];
        stringstream ss;
        ss << "index data: "
           << " tkr: " << indexData.szWindCode
           << " tme: " << indexData.nTime
           << " lastPrc: " << indexData.nLastIndex
           << " endl\n";
        fwrite(ss.str().c_str(), sizeof(char), ss.str().length(), pFile_ );
    }
    return 0;
}
int HfsTickSourceHHApi::process_transaction(TDF_TRANSACTION *pTrans, unsigned int cnt) {
    for (unsigned int i = 0; i < cnt; ++i){
        const TDF_TRANSACTION &transaction = pTrans[i];
        stringstream ss;
        ss << "ts data: "
           << " tkr: " << transaction.szWindCode
           << " tme: " << transaction.nTime
           << " nIndex: " << transaction.nIndex
           << " nPrice: " << transaction.nPrice
           << " nVolume: " << transaction.nVolume
           << " nTurnover: " << transaction.nTurnover
           << " nBSFlag: " << transaction.nBSFlag
           << " chOrderKind: " << transaction.chOrderKind
           << " chFunctionCode: " << transaction.chFunctionCode
           << " nAskOrder: " << transaction.nAskOrder
           << " nBidOrder: " << transaction.nBidOrder
           << " endl\n";
        fwrite(ss.str().c_str(), sizeof(char), ss.str().length(), pFile_);
    }
    return 0;
}
int HfsTickSourceHHApi::process_order(TDF_ORDER *pOrder, unsigned int cnt) {
    for (unsigned int i = 0; i < cnt; ++i){
        const TDF_ORDER &order = pOrder[i];
        stringstream ss;
        ss << "order data: "
           << " tkr: " << order.szWindCode
           << " tme: " << order.nTime
           << " nOrder: " << order.nOrder
           << " prc: " << order.nPrice
           << " vol: " << order.nVolume
           << " kind: " << order.chOrderKind
           << " chFunctionCode: " << order.chFunctionCode
           << " endl\n";
        fwrite(ss.str().c_str(), sizeof(char), ss.str().length(), pFile_);
    }
    return 0;
}
int HfsTickSourceHHApi::process_order_queue(TDF_ORDER_QUEUE *pQueue, unsigned int cnt) {
    for (unsigned int i = 0; i < cnt; ++i){
        const TDF_ORDER_QUEUE &orderQueue = pQueue[i];
        stringstream ss;
        ss << "orderqueue data: "
           << " tkr: " << orderQueue.szWindCode
           << " tme: " << orderQueue.nTime
           << " nSide: " << orderQueue.nSide
           << " nPrice: " << orderQueue.nPrice
           << " nOrders: " << orderQueue.nOrders
           << " nOrder: " << orderQueue.nABItems
           << " endl\n";
        fwrite(ss.str().c_str(), sizeof(char), ss.str().length(), pFile_);
    }
    return 0;
}
int HfsTickSourceHHApi::process_future_data(TDF_FUTURE_DATA *pFuture, unsigned int cnt) {
    
    return 0;
}

void on_recv_data(THANDLE hTdf, TDF_MSG *pMsgHead) {
    if (!hTdf || !pMsgHead || !pMsgHead->pData) {
        return;
    }
    unsigned int nItemCount = pMsgHead->pAppHead->nItemCount;
    unsigned int nItemSize = pMsgHead->pAppHead->nItemSize;
    if (!nItemCount) {
       return ;
   }
   HfsTickSourceHHApi* api = HfsTickSourceHHApi::getInstance();
   switch(pMsgHead->nDataType) {
        case MSG_DATA_MARKET: {
            api->process_market_data((TDF_MARKET_DATA *)pMsgHead->pData, nItemCount);
        }
        break;
        case MSG_DATA_FUTURE:{
            api->process_future_data((TDF_FUTURE_DATA *)pMsgHead->pData, nItemCount);
        }
        break;
        case MSG_DATA_INDEX: {
            api->process_index_data((TDF_INDEX_DATA *)pMsgHead->pData, nItemCount);
        }
        break;
        case MSG_DATA_TRANSACTION: {
            api->process_transaction((TDF_TRANSACTION *)pMsgHead->pData, nItemCount);
        }
        break;
        case MSG_DATA_ORDERQUEUE: {
            api->process_order_queue((TDF_ORDER_QUEUE *)pMsgHead->pData, nItemCount);
            // TDF_ORDER_QUEUE* pLastOrderQueue = GETRECORD(pMsgHead->pData,TDF_ORDER_QUEUE, nItemCount-1);
            // printf( "接收到委托队列记录:代码：%s, 业务发生日:%d, 时间:%d, 委托价格:%d，订单数量:%d \n", pLastOrderQueue->szWindCode, pLastOrderQueue->nActionDay, pLastOrderQueue->nTime, pLastOrderQueue->nPrice, pLastOrderQueue->nOrders);
        }
        break;
        case MSG_DATA_ORDER:{
            api->process_order((TDF_ORDER *)pMsgHead->pData, nItemCount);
        }
        break;
        default:{
           
        }
        break;
   }
}

void on_recv_sys(THANDLE hTdf, TDF_MSG* pSysMsg){
    if (!pSysMsg || !hTdf) {
        return;
    }
    switch (pSysMsg->nDataType) {
        case MSG_SYS_DISCONNECT_NETWORK:{
            FLOG << "MSG_SYS_DISCONNECT_NETWORK";
            HfsTickSourceHHApi::getInstance()->stop();
        }
        break;
        case MSG_SYS_CONNECT_RESULT:{
            TDF_CONNECT_RESULT *pConnResult = (TDF_CONNECT_RESULT *)pSysMsg->pData;
            if (pConnResult && pConnResult->nConnResult){
                TLOG << "connect success" ;
            } else {
                TLOG << "connect failed";
                HfsTickSourceHHApi::getInstance()->stop();
            }
        }
        break;
        case MSG_SYS_LOGIN_RESULT:{
            TDF_LOGIN_RESULT *pLoginResult = (TDF_LOGIN_RESULT *)pSysMsg->pData;
            if (pLoginResult && pLoginResult->nLoginResult) {
                printf("login suc:info:%s, nMarkets:%d\n", pLoginResult->szInfo, pLoginResult->nMarkets);
                for (int i = 0; i < pLoginResult->nMarkets; i++) {
                    printf("market:%s, dyn_date:%d\n", pLoginResult->szMarket[i], pLoginResult->nDynDate[i]);
                }
            } else {
                printf("login fail:%s\n", pLoginResult->szInfo);
                HfsTickSourceHHApi::getInstance()->stop();
            }
        }
        break;
        case MSG_SYS_CODETABLE_RESULT: {
            TDF_CODE_RESULT *pCodeResult = (TDF_CODE_RESULT *)pSysMsg->pData;
            if (pCodeResult) {
                printf("get codetable:info:%s, num of market:%d\n", pCodeResult->szInfo, pCodeResult->nMarkets);
                for (int i = 0; i < pCodeResult->nMarkets; i++) {
                    printf("market:%s, codeCount:%d, codeDate:%d\n", pCodeResult->szMarket[i], pCodeResult->nCodeCount[i], pCodeResult->nCodeDate[i]);

                    if (1) {
                        //CodeTable
                        TDF_CODE *pCodeTable;
                        unsigned int nItems;
                        TDF_GetCodeTable(hTdf, pCodeResult->szMarket[i], &pCodeTable, &nItems);
                        printf("nItems =%d\n", nItems);
                        HfsTickSourceHHApi::getInstance()->process_code_table(pCodeTable, nItems);
                        // for (unsigned int i = 0; i < nItems; i++) {
                        //     TDF_CODE &code = pCodeTable[i];
                        //     printf("windcode:%s, code:%s, market:%s, name:%s, nType:0x%x\n", code.szWindCode, code.szCode, code.szMarket, code.szCNName, code.nType);
                        // }
                        TDF_FreeArr(pCodeTable);
                    }
                }
            }
        }
        break;
        case MSG_SYS_QUOTATIONDATE_CHANGE: {
            TDF_QUOTATIONDATE_CHANGE *pChange = (TDF_QUOTATIONDATE_CHANGE *)pSysMsg->pData;
            if (pChange) {
                printf("MSG_SYS_QUOTATIONDATE_CHANGE: market:%s, nOldDate:%d, nNewDate:%d\n", pChange->szMarket, pChange->nOldDate, pChange->nNewDate);
            }
        }
        break;
        case MSG_SYS_MARKET_CLOSE:{
            TDF_MARKET_CLOSE *pCloseInfo = (TDF_MARKET_CLOSE *)pSysMsg->pData;
            if (pCloseInfo){
                TLOG << "MSG_SYS_MARKET_CLOSE";
                HfsTickSourceHHApi::getInstance()->stop();
            }
        }
        break;
        case MSG_SYS_HEART_BEAT: {
            TLOG << "MSG_SYS_HEART_BEAT...............";
        }
        break;
        default:
            //assert(0);
            break;
    }
}
