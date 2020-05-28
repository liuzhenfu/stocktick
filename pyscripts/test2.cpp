
//希望按每个股票存成“1110委托成交000001.csv”的格式
//股票代码是“00xxxx”或“30xxxx”，如果没有这个股票（或者这个股票停牌，没有委托成交信息），则不创建文件 


#include <iostream>
using namespace std;
#include <stdio.h>
#include <stdlib.h>
#include <map>
#include "HfsTick.hpp"
int main(int argc, char **argv)
{

    FILE * pFile;
    long lSize;
    char * buffer;
    size_t result;
    char datName[256] = {0};
    sprintf(datName, "/datas/share/stockdata/L2data/SZ_N/HHTICK_%s.dat", argv[1]);
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
    map<int, string> codeMap;
    map<string, string> fileMap;  // 
    
    map<string, string> mktMap;  // 
    map<string, string> lastMktMap;
    for (int i = 0; i < schead->nCount; ++i) {
        hfs_sc_t *sc = ((hfs_sc_t *)(buf + sizeof(hfs_sc_head_t))) + i;
        //cout << sc->chSecurityCode << endl;
        codeMap[sc->gid] = string(sc->chSecurityCode);
    }
    int mkcnt = 0;
    int transcnt =0;
    int indexcnt = 0;
    int ordercnt = 0;
    int orderqueuecnt = 0;
    int fastcnt = 0;

    //FILE* wOut = fopen("1110委托成交000001.csv","w+"); 
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
            //cout << " == data == sz != nDataLen " << sz << " " << head.nDataLen << endl;
            //cout << head.nTime << endl;
            //cout << " type:" << head.sDataType << endl;
            ///cout << "len : " <<head.nDataLen << endl;
            if (feof(pFile)) cout << "end of file "  << endl;
            //break;
        }
        int N = 0;
        char out[256] = {0};
        int out_n = 0;
        //cout << head.sDataType << endl;
       switch (head.sDataType) {
        
        case ID_TDFTELE_ORDER:
          N = ((TDFDefine_OrderHead *)buf)->nItems;
             for (int i = 0; i < N; ++i) {
                TDFDefine_Order *md = ((TDFDefine_Order *)(buf + sizeof(TDFDefine_OrderHead))) + i;
                if (md->nTime < 95000000 || md->nTime > 100000000) continue;
                map<int,string>::iterator iter = codeMap.find(((TDFDefine_OrderHead *)buf)->gid);
                if (iter == codeMap.end()) { cout << "1 unknown gid : " << ((TDFDefine_OrderHead *)buf)->gid << endl; continue;}
                string tkr = iter->second;
                if (!((tkr[0]=='0' && tkr[1]=='0') || (tkr[0]=='3' && tkr[1]=='0'))) continue;
                if (md->chType == '0' && md->chBSFlag == 'B')
                    out_n = sprintf(out, "%d,%d,%d,%d,%d\n",
                                    md->nTime, md->nPrice, md->nVolume, md->nIndex, 0);
                if (md->chType == '0' && md->chBSFlag == 'S')
                    out_n = sprintf(out, "%d,%d,%d,%d,%d\n",
                                    md->nTime, md->nPrice, md->nVolume, 0, md->nIndex);
                if (md->chType=='1' && md->chBSFlag=='B')
                    out_n = sprintf(out, "%d,%d,%d,%d,%d\n",
                                    md->nTime,200,md->nVolume,md->nIndex,0);
                if (md->chType=='1' && md->chBSFlag=='S')
                    out_n = sprintf(out, "%d,%d,%d,%d,%d\n",
                                    md->nTime,200,md->nVolume,0,md->nIndex);
               if (md->chType=='U' && md->chBSFlag=='B')
                    out_n = sprintf(out, "%d,%d,%d,%d,%d\n",
                                    md->nTime,100,md->nVolume,md->nIndex,0);
                if (md->chType=='U' && md->chBSFlag=='S')
                    out_n = sprintf(out, "%d,%d,%d,%d,%d\n",
                                    md->nTime,100,md->nVolume,0,md->nIndex);
                sprintf(out, "od:%s,%d,%d,%d,%d,%c,%c\n",
                tkr.c_str(), md->nTime, md->nIndex, md->nPrice, md->nVolume, md->chType, md->chBSFlag=='\0'?' ':md->chBSFlag);
                map<string, string>::iterator iter2 = fileMap.find(tkr);
                if (iter2 == fileMap.end()){
                    //char fname[125] = {0};
                    //sprintf(fname, "./res/%d委托成交%s", dte, tkr.c_str());
                    //fileMap[tkr] = fopen(fname, "w+");
                    //cout << fname << endl;
                    fileMap[tkr] = string(out);
                }
                else {
                    fileMap[tkr] += string(out);
                }
                //if (!fileMap[tkr]){
                    //cout << tkr << "file create failed" << endl;
                //}
                //fwrite(out, sizeof(char), out_n, fileMap[tkr]);
             }
            break; 				                                                           
        case ID_TDFTELE_TRANSACTIONEX:
            N = ((TDFDefine_TransactionExHead *)buf)->nItems;
            for (int i = 0; i < N; ++i) {
               TDFDefine_TransactionEx *ts = ((TDFDefine_TransactionEx *)(buf + sizeof(hfs_transaction_head_t))) + i;
               if (ts->nTime < 95000000 || ts->nTime > 100000000) continue;
               map<int,string>::iterator iter = codeMap.find(((TDFDefine_TransactionExHead *)buf)->gid);
               if (iter == codeMap.end()) { cout << "2 unknown gid : " << ((TDFDefine_TransactionExHead *)buf)->gid << endl; continue;}
               string tkr = iter->second;
               if (!((tkr[0]=='0' && tkr[1]=='0') || (tkr[0]=='3' && tkr[1]=='0')))
                   continue;
               out_n = sprintf(out, "ts:%s,%d,%d,%d,%d,%d,%c,%c,%c,%d,%d\n",
                tkr.c_str(), ts->nTime, ts->nIndex, ts->nPrice, ts->nVolume, ts->nTurnover, 
                ts->chBSFlag=='\0'?' ':ts->chBSFlag, ts->chOrderKind=='\0'?' ':ts->chOrderKind,
                ts->chFunctionCode=='\0'?' ':ts->chFunctionCode, 
                ts->nAskOrder, ts->nBidOrder);
               map<string, string>::iterator iter2 = fileMap.find(tkr);
               if (iter2 == fileMap.end()){
                   fileMap[tkr] = string(out);
               }
               else {
                   fileMap[tkr] += string(out);
               }
        	}
            break;
        case ID_TDFTELE_MARKETDATA:
            N = *(int *)buf;
            for(int i=0;i<N;i++) {
                TDFDefine_MarketData *md = ((TDFDefine_MarketData *)(buf+sizeof(int))) + i;
                if (md->nTime < 95000000 || md->nTime > 100000000) continue;
                map<int,string>::iterator iter = codeMap.find(md->gid);
                if (iter == codeMap.end()) { cout << "3 unknown gid : " << md->gid << endl; continue;}
                string tkr = iter->second;
                //if (!((tkr[0] == '6' && tkr[1] == '0')))
                    //continue;
                //out_n = sprintf(out, "%d,%d,%d,%d\n",
                //                   md->nTime,md->nMatch,md->nBidPrice[0],md->nAskPrice[0]);
                //map<string, string>::iterator iter2 = mktMap.find(tkr);
                //if (iter2 == mktMap.end()){
                //    mktMap[tkr] = string(out);
                //}
                //else {
                //    mktMap[tkr] += string(out);
                //}
                out_n = sprintf(out, "md:%s,%d,%d,%d,%d,%d,%d,%d,"
                     "%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,"
                     "%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,"
                     "%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,"
                     "%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,"
                     "%d,%lld,%lld,%lld,%lld,%d,%d,%d,%d,%d,%d\n",
                tkr.c_str(), md->nTime, md->nStatus, md->nPreClose, md->nOpen, md->nHigh, md->nLow, md->nMatch,
                md->nAskPrice[0], md->nAskPrice[1], md->nAskPrice[2], md->nAskPrice[3], md->nAskPrice[4], md->nAskPrice[5], md->nAskPrice[6], md->nAskPrice[7], md->nAskPrice[8], md->nAskPrice[9],
                md->nAskVol[0], md->nAskVol[1], md->nAskVol[2], md->nAskVol[3], md->nAskVol[4], md->nAskVol[5], md->nAskVol[6], md->nAskVol[7], md->nAskVol[8], md->nAskVol[9],
                md->nBidPrice[0], md->nBidPrice[1], md->nBidPrice[2], md->nBidPrice[3], md->nBidPrice[4], md->nBidPrice[5], md->nBidPrice[6], md->nBidPrice[7], md->nBidPrice[8], md->nBidPrice[9],
                md->nBidVol[0], md->nBidVol[1], md->nBidVol[2], md->nBidVol[3], md->nBidVol[4], md->nBidVol[5], md->nBidVol[6], md->nBidVol[7], md->nBidVol[8], md->nBidVol[9],
                md->nNumTrades, md->iVolume, md->iTurnover, md->nTotalBidVol, md->nTotalAskVol, md->nWeightedAvgBidPrice, md->nWeightedAvgAskPrice, 
                md->nIOPV, md->nYieldToMaturity, md->nHighLimited, md->nLowLimited);
                map<string, string>::iterator iter2 = fileMap.find(tkr);
                if (iter2 == fileMap.end()){
                   fileMap[tkr] = string(out);
               }
               else {
                   fileMap[tkr] += string(out);
               }
            }
            break;
        case ID_TDFTELE_ADDCODE:
            //TDFDefine_SecurityCode* pHDFCode = (TDFDefine_SecurityCode*)(buf);
            cout << "add code " << ((TDFDefine_SecurityCode*)(buf))->gid << endl;
            break;
        case ID_TDFTELE_MARKETDATA_FUTURES:
            N = *(int *)buf;
            for(int i=0;i<N;i++) {
                TDFDefine_MarketData_Futures *md = ((TDFDefine_MarketData_Futures *)(buf+sizeof(int))) + i;
                map<int,string>::iterator iter = codeMap.find(md->gid);
                if (iter == codeMap.end()) { cout << "4 unknown gid : " << md->gid << endl; continue;}
                string tkr = iter->second;
                cout << tkr << "  "<< md->nMatch << endl;
                
            }
            break;
        default:
            break;
        }
    }
    string strHead = "tme,prc,vol,bod,aod\n";
    for (map<string, string>::iterator iter = fileMap.begin(); iter != fileMap.end(); ++iter){
        char fname[125] = {0};
        sprintf(fname, "./res/%d委托成交%s.csv", dte, iter->first.c_str());
        FILE* pout = fopen(fname, "w+");
        fwrite(strHead.c_str(), strHead.length(), 1, pout);
        fwrite(iter->second.c_str(), iter->second.length(), 1, pout);
        string lastMkt = lastMktMap.find(iter->first)!=lastMktMap.end()?lastMktMap[iter->first]:"";
        fwrite(lastMkt.c_str(), lastMkt.length(), 1, pout);
        fclose(pout);
    }
    strHead = "tme,prc,bid1,ask1\n";
    for (map<string, string>::iterator iter = mktMap.begin(); iter != mktMap.end(); ++iter){
        char fname[125] = {0};
        sprintf(fname, "./res/%d_mkt_%s.csv", dte, iter->first.c_str());
        FILE* pout = fopen(fname, "w+");
        fwrite(strHead.c_str(), strHead.length(), 1, pout);
        fwrite(iter->second.c_str(), iter->second.length(), 1, pout);
        fclose(pout);
    }

    fclose(pFile);
    cout << "read done" << endl;
    //fclose(wOut);
    system("pause");
    return 0;
}