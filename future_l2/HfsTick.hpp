#pragma once

#include <iostream>
#include <map>
#include <string>
#include <vector>
#include <cstring>
#include <boost/serialization/singleton.hpp>

//֤ȯ���Ͷ���
#define ID_BT_INDEX                 0x01   //������ָ��
#define ID_BT_SHARES_A              0x10   //A��
#define ID_BT_ZXB                   0x11   //��С��
#define ID_BT_CYB                   0x12   //��ҵ��
#define ID_BT_FUND_ETF              0x23   //ETF
#define ID_BT_BOND_CORP             0x31   //��ҵծȯ
#define ID_BT_FUTURES_IDX           0x70   //ָ���ڻ�

//�������Ͷ���
#define ID_TDFTELE_LOGIN			1		//��¼(Login)
#define ID_TDFTELE_LOGINANSWER		2		//��¼Ӧ��
#define ID_TDFTELE_LOGOUT			3		//�ǳ�(Logout)
#define ID_TDFTELE_CLOSE			4		//�������ر�(Server Close)
#define ID_TDFTELE_COCDETABLE		6		//֤��������(Security Directory)
#define ID_TDFTELE_REQDATA			7		//������������
#define ID_TDFTELE_MARKETCLOSE		8		//������Ϣ	
#define ID_TDFTELE_TRADINGMESSAGE	9		//������Ϣ
#define ID_TDFTELE_TRANSACTION		1101	//�ɽ�(Transaction)
#define ID_TDFTELE_ORDERQUEUE		1102	//ί�ж���(Queue)
#define ID_TDFTELE_ORDER			1103	//���ί��(Order)
#define ID_TDFTELE_ORDERQUEUE_FAST	1104	//ί�ж���(FAST Queue)
#define ID_TDFTELE_TRANSACTIONEX    1105    //��ʳɽ���չ 
#define ID_TDFTELE_MARKETDATA		1012	//��������(Market Data)
#define ID_TDFTELE_MARKETDATA_FUTURES	1016	//�ڻ���������(Futures Market Data)	1016
#define ID_TDFTELE_INDEXDATA		1113	//ָ��(Index)
#define ID_TDFTELE_MARKETOVERVIEW	1115	//�г��ſ�(Market Overview)
#define ID_TDFTELE_ETFLISTFILE		1116	//ETF�嵥�ļ�.


#define ID_TDFTELE_ADDCODE			2001	//��Ӵ���.
#define ID_TDFTELE_SUBSCRIPTION		2002	//��������.
#define ID_TDFTELE_PLAYSPEED		2003	//���ݻط��ٶ�����.
#define ID_TDFTELE_REQETFLIST		2004	//����ETF�嵥.

#pragma pack(push,1)

#ifdef __linux__
typedef long long __int64;
#endif

struct TDFDefine_MsgHead
{
    unsigned short  	sFlags;		//16�ֽ� ��ʶ��,������ TDF_VERSION_NX_START_6001 .
    unsigned short  	sDataType;	//16�ֽ� ��������	          
    int					nDataLen;	//32�ֽ� ���ݳ���
    int					nTime;		//32�ֽ� ʱ�������ȷ������HHMMSSmmmm��
    int     			nOrder;		//32�ֽ� ��ˮ��
};

struct TDFDefine_Login
{
    char chUserName[16];
    char chPassword[32];
    char chID[8];
    char chMD5[32];
};

struct TDFDefine_LoginAnswer
{
    char chInfo[64];			//��Ϣ
    int  nAnswer;				//1:��½�ɹ�
    int  nMarkets;
    char chMarketFlag[32][4];	//�г���־
    int  nDynDate[32];			//��̬��������
};

struct TDFDefine_RequestCodeTable
{
    char chMarketFlag[4];		//�г���־(SZ;SH;HK;CF)
    int  nDate;					//�������ڣ�-1:��ʾ��̬���ݣ�
};

#define ID_HDFDATAFLAGS_RETRANSALTE			0x00000001	//���ݴӿ�ʼ����
#define ID_HDFDATAFLAGS_NOTRANSACTION		0x00000100	//��������ʳɽ�����
#define ID_HDFDATAFLAGS_NOABQUEUE			0x00000200	//������ί�ж�������
#define ID_HDFDATAFLAGS_NOINDEX				0x00000400	//������ָ������
#define ID_HDFDATAFLAGS_NOMARKETOVERVIEW	0x00000800	//������ Market OverView ����
#define ID_HDFDATAFLAGS_NOORDER				0x00001000	//���������ί�����ݣ�SZ-Level2��
#define ID_HDFDATAFLAGS_COMPRESSED			0x00010000	//��������ѹ��
#define ID_HDFDATAFLAGS_ABQUEUE_FAST		0x00020000	//��FAST��ʽ�ṩί�ж�������
#define ID_HDFDATAFLAGS_TRANSACTIONEX       0x00080000  //��ʳɽ�����չ��ʽ���ͣ���ί����Ϣ��
#define ID_HDFDATAFLAGS_DBF1                0x08000000  //������DBF����ר��Э��


struct TDFDefine_RequestMarketData{
    char chMarketFlag[4];		
    int  nFlags;              //
};


struct TDFDefine_SecurityCodeHead{
    int  nSource;	//������ 0:���� 2:�Ϻ�
    int  nDate;		//��������
    int  nCount;	//��������(-1:δ��Ȩ)
    int  nFlags;	//(����)
};

struct TDFDefine_SecurityCode{
    int  gid;	
    int  nType;	
    char chSecurityCode[8];
    char chSymbol[16];		
};

//1.1.2 ��ʳɽ�(Transaction)
struct TDFDefine_TransactionHead
{
    int 	gid;			//���ձ��
    int     nItems;			//���ݸ���
};

struct TDFDefine_Transaction{
    int 	nTime;		//�ɽ�ʱ��(HHMMSSmmmm)
    int 	nIndex;		//�ɽ����
    int		nPrice;		//�ɽ��۸�
    int 	nVolume;	//�ɽ�����
    int		nTurnover;	//�ɽ����
};

//��ʳɽ���չ(TransactionEx)
struct TDFDefine_TransactionExHead
{
    int gid;    //���ձ��
    int nItems; //���ݸ���
};
struct TDFDefine_TransactionEx
{
    int nTime;           //�ɽ�ʱ��(HHMMSSmmm)
    int nIndex;          //�ɽ����
    int nPrice;          //�ɽ��۸�
    int nVolume;         //�ɽ�����
    int nTurnover;       //�ɽ����
    char chBSFlag;       //��������
    char chOrderKind;    //�ɽ�����
    char chFunctionCode; //�ɽ�����
    char chResv;         //����
    int nAskOrder;       //������ί�����
    int nBidOrder;       //����ί�����
};

//1.1.2 ���ί��(Order)
struct TDFDefine_OrderHead
{
    int 	gid;			//���ձ��
    int     nItems;			//���ݸ���
};

struct TDFDefine_Order
{
    int 	nTime;		//ί��ʱ��(HHMMSSmmmm)
    int 	nIndex;		//ί�б��
    int		nPrice;		//ί�м۸�
    int 	nVolume;	//ί������
    char    chType;		//ί�����
    char    chBSFlag;	//ί����������('B','S','C')
    char    chResv[2];	//����	
};

//1.1.3 ��������(Queue)
struct TDFDefine_OrderQueueHead
{
    int     nItems;			//���ݸ���
};

struct TDFDefine_OrderQueue{
    int 	gid;			//���ձ��
    int 	nTime;			//�������(HHMMSSmmmm)
    int     nSide;			//��������('B':Bid 'S':Ask)
    int		nPrice;			//�ɽ��۸�
    int 	nOrders;		//��������
    int 	nABItems;		//��ϸ����
    int 	nABVolume[200];	//������ϸ
};

//1.1.3.1 ��������(�Ϻ�FAST Queue)
struct TDFDefine_OrderQueue_FAST
{
    int  gid;			//���ձ��
    int  nTime;				//����ʱ�䣨HHMMSS��
    int  nSide;				//��������'B':Bid 'A':Ask��
     int  nImageStatus;		//����״̬��1-Full Image 2-Update��
    int  nNoPriceLevel;		//�����ļ�λ��
}; 

struct TDFDefine_OrderQueue_FAST_Operate
{
    int		nPriceOperate;	// 1.add , 2 Update ,3 Delete  0. absent 
    int     nPrice;			//�۸�
    int		nNumOrders;		//ί�б���
    int		nOqLevel;		//��ǰ��λ��Ҫ�����Ķ�����
};

struct TDFDefine_OrderQueue_FAST_OperateItem
{
    int nOperate;	//������ʽ: 1 Add ,2 Update,3 Delete
    int nEntryID;   //����ID:  Oreder Queue Operator Entry ID
    int nQty;		//��������
};

//1.1.4 ��������(Market Data)
struct TDFDefine_MarketDataHead
{
    int     nItems;			//���ݸ���
};

typedef TDFDefine_MarketDataHead TDFDefine_MarketDataFuturesHead;

struct TDFDefine_MarketData
{
    int		gid;						//���ձ��
    int		nTime;						//ʱ��(HHMMSSmmmm)
    int		nStatus;					//״̬
    unsigned int nPreClose;				//ǰ���̼�
    unsigned int nOpen;					//���̼�
    unsigned int nHigh;					//��߼�
    unsigned int nLow;					//��ͼ�
    unsigned int nMatch;				//���¼�
    unsigned int nAskPrice[10];			//������
    unsigned int nAskVol[10];			//������
    unsigned int nBidPrice[10];			//�����
    unsigned int nBidVol[10];			//������
    unsigned int nNumTrades;			//�ɽ�����
    __int64	iVolume;					//�ɽ�����
    __int64	iTurnover;					//�ɽ��ܽ��
    __int64	nTotalBidVol;				//ί����������
    __int64	nTotalAskVol;				//ί����������
    unsigned int nWeightedAvgBidPrice;	//��Ȩƽ��ί��۸�
    unsigned int nWeightedAvgAskPrice;  //��Ȩƽ��ί���۸�
    int		nIOPV;						//IOPV��ֵ��ֵ
    int		nYieldToMaturity;			//����������
    unsigned int nHighLimited;			//��ͣ��
    unsigned int nLowLimited;			//��ͣ��
    char	chPrefix[4];				//֤ȯ��Ϣǰ׺
};

//1.1.5 ָ��(Index)
struct TDFDefine_IndexDataHead
{
    int     nItems;				//���ݸ���
};

struct TDFDefine_IndexData
{
    int		gid;			//���ձ��
    int     nTime;			//ʱ��(HHMMSSmmmm)
    int		nOpenIndex;		//����ָ��
    int 	nHighIndex;		//���ָ��
    int 	nLowIndex;		//���ָ��
    int 	nLastIndex;		//����ָ��
    __int64	iTotalVolume;	//���������Ӧָ���Ľ�������
    __int64	iTurnover;		//���������Ӧָ���ĳɽ����
    int		nPreCloseIndex;	//ǰ��ָ��
};


//1.1.6 �г��ſ�(Market Overview)
struct TDFDefine_MarketOverview
{
    int		nSource;
    int		nOrigTime;			//ʱ��(HHMMSSmmmm)
    int		nOrigDate;			//����
    char	chEndOfDayMarket;	//������־
};


//f)	����(Close)
struct TDFDefine_MarketClose
{
    int		nSource;
    int		nTime;				//ʱ��(HHMMSSmmmm)
    char	chInfo[64];			//������Ϣ
};

//g)	������Ϣ֪ͨ (Trading Message)
struct TDFDefine_TradingMessage
{
    int		gid;				//���ձ��
    char	chSecurityId[8];	//֤ȯ����
    char	chInfo[128];		//��Ϣ
    int		nTime;				//ʱ��(HHMMSSmmmm)
};


//�ڻ�Markets Data.
struct TDFDefine_MarketData_Futures
{
    int gid;							//���ձ��
    int	nTime;							//ʱ��(HHMMSSmmmm)	
    int		nStatus;					//״̬
    __int64 iPreOpenInterest;			//��ֲ�
    unsigned int nPreClose;				//�����̼�
    unsigned int nPreSettlePrice;		//�����
    unsigned int nOpen;					//���̼�	
    unsigned int nHigh;					//��߼�
    unsigned int nLow;					//��ͼ�
    unsigned int nMatch;				//���¼�
    __int64	iVolume;					//�ɽ�����
    __int64	iTurnover;					//�ɽ��ܽ��
    __int64 iOpenInterest;				//�ֲ�����
    unsigned int nClose;				//������
    unsigned int nSettlePrice;			//�����
    unsigned int nHighLimited;			//��ͣ��
    unsigned int nLowLimited;			//��ͣ��
    int		nPreDelta;			        //����ʵ��
    int     nCurrDelta;                 //����ʵ��
    unsigned int nAskPrice[5];			//������
    unsigned int nAskVol[5];			//������
    unsigned int nBidPrice[5];			//�����
    unsigned int nBidVol[5];			//������
};

#pragma pack(pop)

/////////////////////////////////////////////////////////////////////////////////////////////////
using namespace std;

typedef TDFDefine_MsgHead           hfs_msg_head_t;
typedef TDFDefine_Login             hfs_login_t;
typedef TDFDefine_LoginAnswer       hfs_login_answer_t;
typedef TDFDefine_RequestCodeTable  hfs_ctrequ_t;
typedef TDFDefine_RequestMarketData hfs_mdrequ_t;
typedef TDFDefine_SecurityCodeHead  hfs_sc_head_t;
typedef TDFDefine_SecurityCode      hfs_sc_t;
// typedef TDFDefine_TransactionHead   hfs_transaction_head_t;
// typedef TDFDefine_Transaction       hfs_transaction_t;
typedef TDFDefine_TransactionExHead   hfs_transaction_head_t;
typedef TDFDefine_TransactionEx       hfs_transaction_t;
typedef TDFDefine_MarketData        hfs_market_data_t;
typedef TDFDefine_MarketData_Futures hfs_market_data_futures_t;
typedef TDFDefine_OrderQueue        hfs_order_queue_t;
typedef TDFDefine_OrderHead         hfs_tdf_order_head_t;
typedef TDFDefine_Order             hfs_tdf_order_t;
typedef TDFDefine_IndexDataHead     hfs_index_head_t;
typedef TDFDefine_IndexData         hfs_index_t;

//�Զ����һ��ȫ��tick�ṹ
enum hfs_update_type_t {
    UPD_UNKNOWN = 0,
    UPD_TRANSACTION,
    UPD_MARKETDATA,
    UPD_ORDERQUEUE,
    UPD_MARKETDATA_FUTURES,
    UPD_INDEX
};

//�������ݵ���Դ
enum hfs_quote_src_t {
    DTYPE_UNK,
    DTYPE_SHL1,
    DTYPE_SHL2,
    DTYPE_SZL1,
    DTYPE_SZL2,
    DTYPE_CFL1,
    DTYPE_CFL2,
    DTYPE_CTP,
};

#pragma pack(push, 1)

struct hfs_tick_t {
    hfs_update_type_t updType;      //��������
    hfs_quote_src_t   srcType;      //������Դ
    int               gid;          //datafeed�еı��
    int               idnum;        //�ڲ�ά���ı��
    int               updTime;      //���賿��ʼ�ĺ�����
    int	              updOrder;		//���µ���ţ����ε���

    union {
        hfs_market_data_t         md;
        hfs_market_data_futures_t mdf;
        hfs_transaction_t         ts;
        hfs_order_queue_t         qu;
    };
};

#pragma pack(pop)

////////////////////////////////////////////////////////////////////////////////////////////////////
struct SecuCode {
    int   gid;          //֤ȯ�ĵ��ձ�ţ���������Դ��ĩβ��ʾ��������10��cf 1��sh 2��sz
    int   idnum;        //֤ȯ��Ψһ��ţ�������ʷ���ݣ�0,δ֪
    char  tkr[16];
    char  tkrName[38];
    int   type;         //֤ȯ���ͣ���Ʊ������ָ����
};

typedef map<int, int>    GidMap;   //gid to secucode map
typedef map<int, int>    IdnumMap; //idnum to secucode map
typedef map<string, int> TkrMap;   //tkr to secucode map

class HfsSecuTable {
public:
    HfsSecuTable():dte(0) { }

    bool addSecu(int gid, int idnum, const char *tkr, const char *tkrName, int type) {
        if(gmap.find(gid) != gmap.end()) return false;

        scodes.push_back(SecuCode());
        int idx = (int)scodes.size() - 1;
        SecuCode &scode = scodes[scodes.size()-1];
        scode.gid = gid;
        scode.idnum = idnum;
        strncpy(scode.tkr, tkr, 16);
        switch(gid%100) {
        case 10:
          strncpy(scode.tkr + strlen(tkr), ".SP", strlen(tkr));
            break;
        case 1:
            strncpy(scode.tkr + 6, ".SH", 4);
            break;
        case 0:
            strncpy(scode.tkr + 6, ".SZ", 4);
            break;
        default:
            break;
        }
        strncpy(scode.tkrName, tkrName, 38);
        scode.type = type;

        gmap[gid] = idx;
        if(idnum > 0)  nmap[idnum] = idx;
        tmap[scode.tkr] = idx;
        return true;
    }

    const SecuCode *getSCByGid(int gid) {
        GidMap::iterator itr = gmap.find(gid);
        return itr == gmap.end() ? NULL : &scodes[0] + itr->second;
    }

    const SecuCode *getSCByIdnum(int idnum) {
        IdnumMap::iterator itr = nmap.find(idnum);
        return itr == nmap.end() ? NULL : &scodes[0] + itr->second;
    }

    const SecuCode *getSCByTkr(string tkr) {
        TkrMap::iterator itr = tmap.find(tkr);
        return itr == tmap.end() ? NULL : &scodes[0] + itr->second;
    }

    const SecuCode *getSCList(const SecuCode *&scList, int &n) {
        n = scodes.size();
        scList = &scodes[0];
        return scList;
    }

    int getDte() const { return dte; }
    int setDte(int dte) {
        return this->dte = dte;
    }

private:
    vector<SecuCode> scodes;
    GidMap   gmap;
    IdnumMap nmap;
    TkrMap   tmap;
    int      dte;
};
