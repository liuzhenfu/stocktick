/*************************************************************************
	> File Name: GlobalData.h
	> Author: ma6174
	> Mail: ma6174@163.com 
	> Created Time: Thu 25 Aug 2016 12:56:09 PM CST
 ************************************************************************/

#ifndef MARKET_DATA_H_
#define MARKET_DATA_H_
#include<iostream>
#include <unordered_map>
//#include "Order.h"
//#include "GlobalData.h"
struct FuturesData{
    char InstrumentID[30];
	int32 AskV1; 
	int32 BidV1; 
	float32 AskP1; 
	float32 BidP1; 
	int32 Volume,OpenInterest;
	double Turnover;
	float32 LastPrice;
    char UpdateTime[20];
    long TradeDay;
    long Timestamp;
    long UpdateMill;

};
struct FuturesDataL2{
    char InstrumentID[30];
	int32 AskV1,AskV2,AskV3,AskV4,AskV5; 
	int32 BidV1,BidV2,BidV3,BidV4,BidV5; 
	int32 IAskV1,IAskV2,IAskV3,IAskV4,IAskV5; 
	int32 IBidV1,IBidV2,IBidV3,IBidV4,IBidV5; 
	float32 AskP1,AskP2,AskP3,AskP4,AskP5; 
	float32 BidP1,BidP2,BidP3,BidP4,BidP5; 
	int32 Volume,OpenInterest;
	double Turnover;
	float32 LastPrice;
    char UpdateTime[20];
    long TradeDay;
    long Timestamp;

};
struct DataHeader{
    uint32 m_nLength;
    uint32 m_nFileSize;
    long m_start;
    long m_end;
    char m_contracts[300];
    char m_sUpdateDate[30];
    bool m_fin;
    bool m_night;

};
template<class Data>
struct MarketData{
    Data* placeholder;
    Data* volatile currentData;
    Data* volatile lastData;
	//StopWatch sw;
	MarketData(){
		placeholder = new Data();
		memset(placeholder,0, sizeof(Data));
        currentData = placeholder;
        lastData = placeholder;
  

	}

};
#endif
