/*************************************************************************
	> File Name: FuturesInfo.h
	> Author: ma6174
	> Mail: ma6174@163.com 
	> Created Time: Fri 24 Feb 2017 01:55:14 PM CST
 ************************************************************************/
#ifndef FUTURES_INFO_H_
#define FUTURES_INFO_H_
#include<iostream>
typedef float float32;
using namespace std;
struct FuturesInfo{
	char sName[30];
	char sProductName[6];
	uint32 nVolumeMul;
	float32 dPriceTick;
	char sExchangeName[6];
    char sEndTime[20];
    float32 dFeeP;
    float32 dFeeC;

};
struct InfoHeader {
    uint32 m_nLength;
    uint32 m_nFileSize;
    char m_sUpdateDate[30];
};

struct DominantInfo{
    long TradeDay;
    char InstrumentId[30];
    char ProductName[6];
    long Volume;
    long OpenInterest;

};

#endif
