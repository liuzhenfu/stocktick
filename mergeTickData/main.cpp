#include <iostream>
using namespace std;
#include <stdio.h>
#include <stdlib.h>
#include <map>
#include "HfsTick.hpp"

bool getNextData(FILE*pFile, hfs_msg_head_t& head, char *buf) {
    if(!feof(pFile)) {
        fread(&head, sizeof(head), 1, pFile); 
        int sz = fread(buf, sizeof(char), head.nDataLen, pFile);
        if (sz != head.nDataLen) {
            cout << "codeinfo == sz != nDataLen " << sz << " " << head.nDataLen << endl;
            return false;
        }
        return true;
    }
    return false ;
}
int getTime(const hfs_msg_head_t& head, char *buf) {
    int t = 153000000;
    int N = 0;
    switch (head.sDataType) {        
        case ID_TDFTELE_ORDER:
            N = ((TDFDefine_OrderHead *)buf)->nItems;
            for (int i = 0; i < N; ++i) {
                TDFDefine_Order *od = ((TDFDefine_Order *)(buf + sizeof(TDFDefine_OrderHead))) + i;
                t = od->nTime;
                break;
            }
            break;
        case ID_TDFTELE_TRANSACTIONEX:
            N = ((TDFDefine_TransactionExHead *)buf)->nItems;
            for (int i = 0; i < N; ++i) {
               TDFDefine_TransactionEx *ts = ((TDFDefine_TransactionEx *)(buf + sizeof(hfs_transaction_head_t))) + i;
               t = ts->nTime;
               break;
            }
            break;
        case ID_TDFTELE_MARKETDATA:
            N = *(int *)buf;
            for(int i=0;i<N;i++) {
                TDFDefine_MarketData *md = ((TDFDefine_MarketData *)(buf+sizeof(int))) + i;
                t = md->nTime;
                break;
            }
            break;
        case ID_TDFTELE_ORDERQUEUE:
            N = *(int *)buf;
            for(int i=0;i<N;i++) {
                TDFDefine_OrderQueue *oq = ((TDFDefine_OrderQueue *)(buf+sizeof(int))) + i;
                t = oq->nTime;
                break;             
            }
            break;
        case ID_TDFTELE_INDEXDATA:
            N = *(int *)buf;
            for(int i=0;i<N;i++) {
                TDFDefine_IndexData *md = ((TDFDefine_IndexData *)(buf+sizeof(int))) + i;
                t = md->nTime;
                break;
            }
            break;
        case ID_TDFTELE_ORDERQUEUE_FAST:
            N = *(int *)buf;
            for(int i=0;i<N;i++) {
                TDFDefine_OrderQueue_FAST *oq = ((TDFDefine_OrderQueue_FAST *)(buf+sizeof(int))) + i;
                t = oq->nTime;
                break;             
            }
            break;
        case ID_TDFTELE_COCDETABLE:
            t = 0;
            break;
        case ID_TDFTELE_ADDCODE:
            t = 1;
            break;
        case ID_TDFTELE_SUBSCRIPTION:
        case ID_TDFTELE_MARKETOVERVIEW:
        case ID_TDFTELE_ETFLISTFILE:
            t = 2;
            break;
        default:
            cout << "unknown type " << head.sDataType << endl;
    }
    return t;
}
int main(int argc, char **argv)
{
    FILE * pFile_SZ;
    FILE * pFile_SH;
    FILE * pFile_merge;
    long lSize;
    char * buffer;
    size_t result;
    char datName[256] = {0};
    sprintf(datName, "/datas/share/stockdata/L2data/SZ_N/HHTICK_%s.dat", argv[1]);
    pFile_SZ = fopen(datName, "rb");
    sprintf(datName, "/datas/share/stockdata/L2data/SH_N/HHTICK_%s.dat", argv[1]);
    pFile_SH = fopen(datName, "rb");
    sprintf(datName, "HHTICK_%s.dat", argv[1]);
    pFile_merge = fopen(datName, "wb+");
    
    if (pFile_SH == NULL || pFile_SZ == NULL) { fputs("File error", stderr); exit(1); }
    
    hfs_msg_head_t head_sh;
    hfs_msg_head_t head_sz;
    char buf_sh[1024*1000] = {0};
    char buf_sz[1024*1000] = {0};
    getNextData(pFile_SH, head_sh, buf_sh);
    getNextData(pFile_SZ, head_sz, buf_sz);
    while (!feof(pFile_SH) && !feof(pFile_SZ)) {
        if (getTime(head_sh, buf_sh) <= getTime(head_sz, buf_sz)) {
            fwrite(&head_sh,sizeof(head_sh), 1, pFile_merge);
            fwrite(buf_sh, head_sh.nDataLen, 1, pFile_merge);
            if (!getNextData(pFile_SH, head_sh, buf_sh))
                break;
        } else {
            fwrite(&head_sz,sizeof(head_sz), 1, pFile_merge);
            fwrite(buf_sz, head_sz.nDataLen, 1, pFile_merge);
            if (!getNextData(pFile_SZ, head_sz, buf_sz)) {
                break;
            }
        }
    }
    while (!feof(pFile_SH)) {
        if (getNextData(pFile_SH, head_sh, buf_sh)){
            fwrite(&head_sh,sizeof(head_sh), 1, pFile_merge);
            fwrite(buf_sh, head_sh.nDataLen, 1, pFile_merge);
        }
    }
    while (!feof(pFile_SZ)) {
        if (getNextData(pFile_SZ, head_sz, buf_sz)){
            fwrite(&head_sz,sizeof(head_sz), 1, pFile_merge);
            fwrite(buf_sz, head_sz.nDataLen, 1, pFile_merge);
        }
    }
    
    
    cout << "read done" << endl;
    //fclose(wOut);
    system("pause");
    return 0;
}