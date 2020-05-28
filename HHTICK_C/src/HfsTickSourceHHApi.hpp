#pragma once

#include "include/TDFAPI.h"
#include "include/NonMDMsgDecoder.h"
#include "include/TDFAPIInner.h"

#include <stdio.h>
#include <assert.h>
#include <string>
#include <iostream>

#define GETRECORD(pBase, TYPE, nIndex) ((TYPE *)((char *)(pBase) + sizeof(TYPE) * (nIndex)))  // 根据数据首地址取第index个数据
#define ELEM_COUNT(arr) (sizeof(arr) / sizeof(arr[0]))
#define SAFE_STR(str) ((str) ? (str) : "")
#define SAFE_CHAR(ch) ((ch) ? (ch) : ' ')

void on_recv_data(THANDLE hTdf, TDF_MSG *pMsgHead);
void on_recv_sys(THANDLE hTdf, TDF_MSG *pMsgHead);

class HfsTickSourceHHApi {
public:
    virtual bool on_bmo();
    virtual bool run();
    virtual bool on_amc();
    char filename_[256];

  public:
    static HfsTickSourceHHApi* getInstance(){
        static HfsTickSourceHHApi api;
        return &api;
    }
    bool loadConfig(const char *configFile);
    virtual ~HfsTickSourceHHApi();
    bool isRunning(){ return reading_;}
    void stop() { reading_ = false; }
    void setDte(int dte) { dte_ = dte; }
    int process_code_table(TDF_CODE *pCodeTable, unsigned int cnt);      // 处理股票代码  cnt:代码数量
    int process_market_data(TDF_MARKET_DATA *pMarket, unsigned int cnt); // 股票行情
    int process_index_data(TDF_INDEX_DATA *pIndex, unsigned int cnt);    // 指数行情
    int process_transaction(TDF_TRANSACTION *pTrans, unsigned int cnt);  // 逐笔成交
    int process_order(TDF_ORDER *pOrder, unsigned int cnt);              // 逐笔委托
    int process_order_queue(TDF_ORDER_QUEUE *pQueue, unsigned int cnt);  // 委托队列
    int process_future_data(TDF_FUTURE_DATA *pFuture, unsigned int cnt); // 期货期权行情
private:
    bool login();
    HfsTickSourceHHApi( );
    
        
private:
    std::string address_;  // 数据源地址
    std::string port_;     // 
    std::string user_;     
    std::string passwd_;
    std::string address_bak_;  // 连接多个服务器时， 另外一个数据源地址
    std::string port_bak_;

private:
    int dte_;     // trading day
    FILE *pFile_; // out file
    bool reading_;
    bool multi_cons_; // 多路连接
    
};