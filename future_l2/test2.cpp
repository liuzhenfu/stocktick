
#include <iostream>
using namespace std;
#include <stdio.h>
#include <stdlib.h>
#include <map>
#include "HfsTick.hpp"
#include "FileMapper.h"
#include "FuturesInfo.h"
#include "MarketData.h"
#include "DFITCL2ApiDataType.h"

using namespace DFITC_L2;

map<int, string> codeMap;
int process_fut_data(char* data);
int transform_md(TDFDefine_MarketData_Futures* mdf, MDBestAndDeep& deepData);
int do_make(char** argv);
int read_test(char ** argv);
int getScaler(string tkr);
int main(int argc, char **argv)
{
    if(argc < 3) {
        printf("usage:%s make/read/describe filename\n", argv[0]);
        return -1;
    }

    if(strcmp(argv[1], "make") == 0) {
        do_make(argv);
    }
    else if(strcmp(argv[1], "read") == 0) {
        read_test(argv);
    }
    
    //system("pause");
    return 0;
}

int do_make(char** argv) {
    FILE * pFile;
    long lSize;
    char * buffer;
    size_t result;
    char datName[256] = {0};
    sprintf(datName, "/datas/share/stockdata/L2data/CF/HHTICK_%s.dat", argv[2]);
    pFile = fopen(datName, "rb");
    if (pFile == NULL) { fputs("File error", stderr); exit(1); }

    hfs_msg_head_t head;
    int total = 0;
    // 读取股票代码信息
    fread(&head, sizeof(head), 1, pFile); 
    char buf[1024 * 1000] = { 0 };
    int sz = fread(buf, sizeof(char), head.nDataLen, pFile);
    total ++;
    if (sz != head.nDataLen) {
        cout << "codeinfo == sz != nDataLen " << sz << " " << head.nDataLen;
        return -1;
    }
    hfs_sc_head_t *schead = (hfs_sc_head_t *)buf;
    int dte = schead->nDate;
    cout << "行情日期" << dte << endl;
    //map<int, string> codeMap;
    //map<string, string> fileMap;  // 
    
    //map<string, string> mktMap;  // 
    //map<string, string> lastMktMap;
    for (int i = 0; i < schead->nCount; ++i) {
        hfs_sc_t *sc = ((hfs_sc_t *)(buf + sizeof(hfs_sc_head_t))) + i;
        //cout << sc->chSecurityCode << endl;
        codeMap[sc->gid] = string(sc->chSecurityCode);
    }
    int mkcnt = 0;
    string outfilename= "out/"+ to_string(dte) +".dat";
    FileMapper<MDBestAndDeep,DataHeader> myfile; 
    myfile.init(outfilename,true,20*32*1024);
    
    // 读取行情数据
    while (!feof(pFile)) {
        //cout << feof(pFile) << endl;
        memset(&head, 0, sizeof(head));
        if (! fread(&head, sizeof(head), 1, pFile)) {
            if (feof(pFile)) cout << "====end of file " << head.nDataLen << endl;
            else{ cout << "error read head " << endl; }
            break;
        }
        sz = fread(buf, sizeof(char), head.nDataLen, pFile);
        total ++;
        if (sz != head.nDataLen) {
            cout << " == data == sz != nDataLen " << sz << " " << head.nDataLen << endl;
            cout << head.nTime << endl;
            cout << " type:" << head.sDataType << endl;
            cout << "len : " <<head.nDataLen << endl;
            if (feof(pFile)) cout << "end of file "  << endl;
            //break;
        }
        int N = 0;
        MDBestAndDeep deepData;
        //char out[256] = {0};
        //int out_n = 0;
        //cout << head.sDataType << endl;
       switch (head.sDataType) {
        case ID_TDFTELE_ADDCODE:
            //TDFDefine_SecurityCode* pHDFCode = (TDFDefine_SecurityCode*)(buf);
            cout << "add code " << ((TDFDefine_SecurityCode*)(buf))->gid << endl;
            break;
        case ID_TDFTELE_MARKETDATA_FUTURES:
            N = *(int *)buf;
            for(int i=0;i<N;i++) {
                TDFDefine_MarketData_Futures *md = ((TDFDefine_MarketData_Futures *)(buf+sizeof(int))) + i;
                map<int,string>::iterator iter = codeMap.find(md->gid);
                if (iter == codeMap.end()) { cout << "unknown gid : " << md->gid << endl; continue;}
                string tkr = iter->second;
                transform_md(md, deepData);
                int scaler = getScaler(tkr);
                if (scaler == -1) {
                    cout << tkr << endl;
                }
                deepData.AvgPrice /= scaler;
                strcpy(deepData.Contract,tkr.c_str());
                strcpy(deepData.TradeDate, to_string(dte).c_str());
                myfile.pushData(&deepData);
            }
            break;
        default:
            cout<< "unknown id " << head.sDataType << endl;
            break;
        }
    }
    cout << "read done" << endl;
}
int process_fut_data(char* data) {
    int N = *(int *)data;
    MDBestAndDeep deepData;
    for(int i=0;i<N;i++) {
        TDFDefine_MarketData_Futures *md = ((TDFDefine_MarketData_Futures *)(data+sizeof(int))) + i;
        map<int,string>::iterator iter = codeMap.find(md->gid);
        if (iter == codeMap.end()) { cout << "unknown gid : " << md->gid << endl; continue;}
        string tkr = iter->second;
        transform_md(md, deepData);
    }
}

string format_tme(int tme){
    unsigned int h = tme / 10000000;
    unsigned int m = tme % 10000000 / 100000;
    unsigned int s = tme % 100000 / 1000;
    unsigned int ms = tme % 1000;
    char buf[16] = {0};
    sprintf(buf, "%d:%d:%d.%d",h, m, s, ms);
    return string(buf);
}
int getScaler(string tkr) {
    if (tkr.find("IC") != std::string::npos) {
        return 200;
    }
    else if (tkr.find("IF") != std::string::npos or tkr.find("IH") != std::string::npos) {
        return 300;
    }
    else if (tkr.find("T") != std::string::npos) {
        return 10000;
    }
    else {
        return -1;
    }
}
int transform_md(TDFDefine_MarketData_Futures* mdf, MDBestAndDeep& deepData) {
    memset(&deepData, 0, sizeof(deepData));
    strcpy(deepData.Exchange,"CF");                          //交易所
    strcpy(deepData.Contract,"");                         //合约代码
    deepData.SuspensionSign = 0;                       //停牌标志
    deepData.LastClearPrice = mdf->nPreSettlePrice/10000.0;         //昨结算价
    deepData.ClearPrice = mdf->nSettlePrice/10000.0;                           //今结算价
    if (mdf->iVolume > 0)
        deepData.AvgPrice = mdf->iTurnover / mdf->iVolume ;                              //成交均价
    deepData.LastClose = mdf->nPreClose / 10000.0;                            //昨收盘
    deepData.Close = mdf->nClose / 10000.0;                                //今收盘
    deepData.OpenPrice = mdf->nOpen / 10000.0;                            //今开盘
    deepData.LastOpenInterest = mdf->iPreOpenInterest;                     //昨持仓量
    deepData.OpenInterest = mdf->iOpenInterest;                         //持仓量
    deepData.LastPrice = mdf->nMatch / 10000.0;                            //最新价
    deepData.MatchTotQty = mdf->iVolume ;                          //成交数量
    deepData.Turnover = mdf->iTurnover;                             //成交金额
    deepData.RiseLimit = mdf->nHigh / 10000.0;                            //最高报价
    deepData.FallLimit = mdf->nLow / 10000.0;                            //最低报价
    deepData.HighPrice = mdf->nHigh / 10000.0;                            //最高价
    deepData.LowPrice = mdf->nLow / 10000.0;                             //最低价
    deepData.PreDelta = mdf->nPreDelta;                             //昨虚实度
    deepData.CurrDelta = mdf->nCurrDelta;                            //今虚实度
    deepData.BuyPriceOne = mdf->nBidPrice[0] / 10000.0;                          //买入价格1
    deepData.BuyQtyOne = mdf->nBidVol[0];                            //买入数量1
    deepData.BuyPriceTwo = mdf->nBidPrice[1] / 10000.0;                          //买入价格2
    deepData.BuyQtyTwo = mdf->nBidVol[1];                            //买入数量2
    deepData.BuyPriceThree = mdf->nBidPrice[2] / 10000.0;                        //买入价格3
    deepData.BuyQtyThree = mdf->nBidVol[2];                          //买入数量3
    deepData.BuyPriceFour = mdf->nBidPrice[3] / 10000.0;                         //买入价格4
    deepData.BuyQtyFour = mdf->nBidVol[3];                           //买入数量4
    deepData.BuyPriceFive = mdf->nBidPrice[4] / 10000.0;                         //买入价格5
    deepData.BuyQtyFive = mdf->nBidVol[4];                           //买入数量5
    deepData.SellPriceOne = mdf->nAskPrice[0] / 10000.0;                         //卖出价格1
    deepData.SellQtyOne = mdf->nAskVol[0];                           //卖出数量1
    deepData.SellPriceTwo = mdf->nAskPrice[1] / 10000.0;                         //卖出价格2
    deepData.SellQtyTwo = mdf->nAskVol[1];                           //卖出数量2
    deepData.SellPriceThree = mdf->nAskPrice[2] / 10000.0;                       //卖出价格3
    deepData.SellQtyThree = mdf->nAskVol[2];                         //卖出数量3
    deepData.SellPriceFour = mdf->nAskPrice[3] / 10000.0;                        //卖出价格4
    deepData.SellQtyFour = mdf->nAskVol[3];                          //卖出数量4
    deepData.SellPriceFive = mdf->nAskPrice[4] / 10000.0;                        //卖出价格5
    deepData.SellQtyFive = mdf->nAskVol[4];                          //卖出数量5
    strcpy(deepData.GenTime, format_tme(mdf->nTime).c_str());                          //行情产生时间
    //deepData.LastMatchQty;                         //最新成交量
    //deepData.InterestChg;                          //持仓量变化
    //deepData.LifeLow;                              //历史最低价
    //deepData.LifeHigh;                             //历史最高价
    //deepData.Delta;                                //delta
    //deepData.Gamma;                                //gama
    //deepData.Rho;                                  //rho
    //deepData.Theta;                                //theta
    //deepData.Vega;                                 //vega
    //deepData.TradeDate;                         //行情日期
}

int read_test(char **argv) {
    char filename[256] = {0};
    sprintf(filename, "./out/%s.dat", argv[2]);
    FileMapper<MDBestAndDeep,DataHeader> myfile;
    myfile.load(filename);
    int num=myfile.getIndex();
    MDBestAndDeep* finfo=myfile.getData();
    for (int i=0;i<num;i++){
        cout << "Exch:" << finfo->Exchange
             << " Contract:" << finfo->Contract
             << " LastClearPrice:" << finfo->LastClearPrice
             << " ClearPrice:" << finfo->ClearPrice
             << " AvgPrice:" << finfo->AvgPrice
             << " LastClose:" << finfo->LastClose
             << " OpenPrice:" << finfo->OpenPrice
             << " LastPrice:" << finfo->LastPrice
             << " MatchTotQty:" << finfo->MatchTotQty
             << " Turnover:" << finfo->Turnover
             << " RiseLimit:" << finfo->RiseLimit
             << " FallLimit:" << finfo->FallLimit
             << " PreDelta:" << finfo->PreDelta
             << " CurrDelta:" << finfo->CurrDelta
             << " BuyPriceOne:" << finfo->BuyPriceOne
             << " BuyQtyOne:" << finfo->BuyQtyOne
             << " SellPriceOne:" << finfo->SellPriceOne
             << " SellQtyOne:" << finfo->SellQtyOne
             << " GenTime:" << finfo->GenTime
             << " TradeDate:" << finfo->TradeDate
             << endl;
        finfo = finfo + 1;
    }
}

// 6214 8301 1885 7902