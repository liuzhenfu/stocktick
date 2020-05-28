#include "HfsTickSourceHH.hpp"
#include <string>
#include <boost/thread.hpp>
#include "xml_parser.hpp"
#include "HfsLog.hpp"

using namespace std;
using namespace boost::asio;
using boost::asio::ip::tcp;

const int COMPANY_CODE = 0x5340;
const int MAX_BUF_SIZE = 1024 * 1024;

HfsTickSourceHH::HfsTickSourceHH(boost::asio::io_service &io, int cdte) 
        : io_service_(io), socket_(io_service_), dte_(cdte){
    msgBuf_.assign(MAX_BUF_SIZE, 0);

    ValidTickCount_ = 0;
    lastCount_ = 0;
    readCount_ = 0;
    reading_ = false;
    curTime_ = 0;
    
}

HfsTickSourceHH::~HfsTickSourceHH() {
    // fclose(pFile_);
}

bool HfsTickSourceHH::loadConfig(const char* configFile){
    a2ftool::XmlNode root_node(configFile);
    a2ftool::XmlNode HH_node = root_node.getChild("HHL2");
    address_ = HH_node.getAttrDefault("HHL2Address","172.18.100.162");
    port_ = HH_node.getAttrDefault("HHL2Port", "20002");
    user_ = HH_node.getAttrDefault("HHL2User", "alpha2fund");
    passwd_ = HH_node.getAttrDefault("HHL2Passwd", "alph1234");
    exchFlag_ = HH_node.getAttrDefault("mktType", "SH;SZ");
    tkrs_ = HH_node.getAttrDefault("SubTkrs", "");
    cout << "address : " << address_
         << "\nport : " << port_
         << "\nusr : " << user_
         << "\nexchFlag : " << exchFlag_ 
         << "\nSubTkrs:" << tkrs_
         << endl;
    // char filename[256] = {0};
    // sprintf(filename, "../data/%s/HHTICK_%d.dat", exchFlag_.c_str(), dte_);
    // cout << filename << endl;
    // pFile_ = fopen(filename, "wb+");
    auto found = tkrs_.find(",");
    while(found != std::string::npos) {
       auto sub_contract = tkrs_.substr(0, found);
       vtkrs_.push_back(sub_contract);
       tkrs_ = tkrs_.substr(found + 1, tkrs_.size() - found - 1);
       found = tkrs_.find(",");
    }
    return true;
}

bool HfsTickSourceHH::login(int mode) {
    tcp::resolver resolver(io_service_);
    tcp::resolver::query query(address_,  port_);
    tcp::endpoint ep = *resolver.resolve(query);

    try {
        socket_.connect(ep);

        size_t sz = 0;
        int msgLen = 0;
        char *mybuf = &msgBuf_[0];

        //login
        hfs_msg_head_t head;
        head.sFlags     = COMPANY_CODE;
        head.sDataType  = 1;
        head.nDataLen   = sizeof(hfs_login_t);
        head.nTime      = 0;
        head.nOrder     = 0;

        hfs_login_t login;
        sprintf(login.chUserName, "%s", user_.c_str());
        sprintf(login.chPassword, "%s", passwd_.c_str());
        login.chID[0] = '\0';
        memcpy(mybuf, &head, sizeof(hfs_msg_head_t));
        memcpy(mybuf+sizeof(hfs_msg_head_t), &login, sizeof(hfs_login_t));

        msgLen = sizeof(hfs_msg_head_t) + sizeof(hfs_login_t);
        sz = boost::asio::write(socket_, boost::asio::buffer(mybuf, msgLen));

        //recv login answer
        msgLen = sizeof(hfs_msg_head_t) + sizeof(hfs_login_answer_t);
        sz = boost::asio::read(socket_, boost::asio::buffer(mybuf, msgLen));
        assert((int)sz == msgLen);
        hfs_login_answer_t &answer = *(hfs_login_answer_t *)(mybuf + sizeof(hfs_msg_head_t));
        if(answer.nAnswer != 1) {
            FLOG << "login error! " << answer.chInfo;
            return false;
        }
        char mktflag[4];
        sprintf(mktflag, exchFlag_.c_str());

        //send codetable request
        head.sFlags    = COMPANY_CODE;
        head.sDataType = 6;
        head.nDataLen  = 0;
        head.nTime     = 0;
        head.nOrder    = 0;
        hfs_ctrequ_t ctreq;
        sprintf(ctreq.chMarketFlag, "%s", mktflag);
        ctreq.nDate = dte_;
        memcpy(mybuf, &head, sizeof(hfs_msg_head_t));
        memcpy(mybuf+sizeof(hfs_msg_head_t), &ctreq, sizeof(hfs_ctrequ_t));
        msgLen = sizeof(hfs_msg_head_t) + sizeof(hfs_ctrequ_t);
        sz = boost::asio::write(socket_, boost::asio::buffer(mybuf, msgLen));

        //recv codetable
        sz = boost::asio::read(socket_, boost::asio::buffer(&head, sizeof(hfs_msg_head_t)));
        assert(sz == sizeof(hfs_msg_head_t) && head.sDataType == ID_TDFTELE_COCDETABLE);
        sz = boost::asio::read(socket_, boost::asio::buffer(mybuf, head.nDataLen));
        assert((int)sz == head.nDataLen);
        process_code_table(&head, mybuf);
        // if(mode == 0) {
            // dte_ = process_code_table(&head, mybuf);
        // }
        // fwrite(&head, sizeof(hfs_msg_head_t), 1, pFile_);
        // fwrite(mybuf, sizeof(char), sz, pFile_);
        {
            hfs_sc_head_t *schead = (hfs_sc_head_t *)mybuf;
            char buf[1024];
            sprintf(buf,  
                "\n===========================LEVEL2行情=========================\n"
                "    数据服务器地址:[ %s ]\n"
                "    数据日期:      [ %d ]\n"
                "    证券数量:      [ %d ]\n"
                "=======================================================================\n\n"
                , socket_.remote_endpoint().address().to_string().c_str(), dte_, schead->nCount);
            ILOG << buf;
        }
        // sub mkt
        if (vtkrs_.size() > 0) {
            head.sFlags = COMPANY_CODE;
            head.sDataType = ID_TDFTELE_SUBSCRIPTION;
            head.nDataLen = sizeof(TDFDefine_SubscriptionHead) + sizeof(TDFDefine_Subscription)*vtkrs_.size();
            head.nTime = 0;
            head.nOrder = 0;

            TDFDefine_SubscriptionHead mdsubHead;
            mdsubHead.nSubscriptionType = 0;
            mdsubHead.nItems = vtkrs_.size();

            //这里，必须同时发送这两个消息包，否则对方的处理逻辑有问题
            memcpy(mybuf, &head, sizeof(hfs_msg_head_t));
            memcpy(mybuf + sizeof(hfs_msg_head_t), &mdsubHead, sizeof(TDFDefine_SubscriptionHead));
            for (int i = 0; i < vtkrs_.size();i++) {
                //cout << "sub tkr " << vtkrs_[i] << endl;
                TDFDefine_Subscription mktsub;
                strcpy(mktsub.chMarket, exchFlag_.c_str());
                strcpy(mktsub.chSymbol, vtkrs_[i].c_str());
                memcpy(mybuf + sizeof(hfs_msg_head_t) + sizeof(TDFDefine_SubscriptionHead) + i * sizeof(TDFDefine_Subscription), &mktsub, sizeof(TDFDefine_Subscription));
            }
            msgLen = sizeof(hfs_msg_head_t) + sizeof(TDFDefine_SubscriptionHead) + sizeof(TDFDefine_Subscription) * vtkrs_.size();
            sz = boost::asio::write(socket_, boost::asio::buffer(mybuf, msgLen));
        }
        //send mktdata request
        head.sFlags    = COMPANY_CODE;
        head.sDataType = 7;
        head.nDataLen  = 0;
        head.nTime     = 0;
        head.nOrder    = 0;

        hfs_mdrequ_t mdreq;
        sprintf(mdreq.chMarketFlag, "%s", mktflag);
        mdreq.nFlags = 0x00080001; //
        //这里，必须同时发送这两个消息包，否则对方的处理逻辑有问题
        memcpy(mybuf, &head, sizeof(hfs_msg_head_t));
        memcpy(mybuf+sizeof(hfs_msg_head_t), &mdreq, sizeof(hfs_mdrequ_t));
        msgLen = sizeof(hfs_msg_head_t) + sizeof(hfs_mdrequ_t);
        sz = boost::asio::write(socket_, boost::asio::buffer(mybuf, msgLen));

        ILOG << "\n" << "准备接收行情数据...";
    }
    catch(std::exception &e) {
        char buf[1024];
        sprintf(buf, 
            "\n******************** 错误 ************************\n"
            "       连接失败:%s\n"
            "***************************************************\n",
            e.what());
        FLOG << buf;
        return false;
    }

    return true;
}

int HfsTickSourceHH::process_code_table(hfs_msg_head_t *head, char *data) {
    hfs_sc_head_t *schead = (hfs_sc_head_t *)data;
    // dte = schead->nDate;
    ILOG << "行情日期：" << schead->nDate;

    // if(HfsSecuTable::get_mutable_instance().getDte() == 0) {
    //     HfsSecuTable::get_mutable_instance().setDte(dte);
    // }

    // int good = 0, bad = 0;
    for(int i=0;i<schead->nCount;i++) {
        hfs_sc_t *sc = ((hfs_sc_t *)(data + sizeof(hfs_sc_head_t))) + i;
        int gid  = sc->gid;
        int type = sc->nType;
        string tkr = sc->chSecurityCode;
        string tkrName = sc->chSymbol;
        if (std::find(std::begin(vtkrs_), std::end(vtkrs_), tkr) != std::end(vtkrs_)) {
            vgids_.insert(make_pair(gid, tkr));
        }
    }
    //     if(type == ID_BT_SHARES_A || type == ID_BT_ZXB || type == ID_BT_CYB || type == ID_BT_FUND_ETF) { //A股，只保留可以取得idnum的股票
    //         const IdnumItem *d = IdnumMgr::get_mutable_instance().queryTkr(tkr.c_str());
    //         if(d != NULL) {
    // int idnum = d->idnum;
    // if(HfsSecuTable::get_mutable_instance().addSecu(gid, idnum, tkr.c_str(), tkrName.c_str(), type)) {
    //     ILOG << "add " << gid << ' ' << idnum << ' ' << type << ' ' << tkr << ' ' << tkrName;
    //     good++;
    // } else {
    //     bad++;
    //     ILOG << "dup " << gid << ' ' << type << ' ' << tkr << ' ' << tkrName;
    // }
    //         }
    //         else {
    // ILOG << "missed " << gid << ' ' << type << ' ' << tkr << ' ' << tkrName;
    // bad++;
    //         }
    //     }
    //     else if(type == ID_BT_INDEX) { //指数，只保留少数几个指数
    //         if(tkr == "999999"    //上证综指
    //  || tkr == "999991" //上证180
    //  || tkr == "000300" //沪深300
    //  ) {
    // int idnum = 0;
    // HfsSecuTable::get_mutable_instance().addSecu(gid, idnum, tkr.c_str(), tkrName.c_str(), type);
    // ILOG << "add " << gid << ' ' << idnum << ' ' << type << ' ' << tkr << ' ' << tkrName;
    // good++;
    //         }
    //         else {
    // bad++;
    //         }
    //     }
    //     else if(type == ID_BT_FUTURES_IDX) { //股指期货，全部保留
    //         static int future_idnum = 0;
    //         HfsSecuTable::get_mutable_instance().addSecu(gid, ++future_idnum, tkr.c_str(), tkrName.c_str(), type);
    //         ILOG << "add " << gid << ' ' << future_idnum << ' ' << type << ' ' << tkr << ' ' << tkrName;
    //         good++;
    //     }
    //     else {
    //         bad++;
    //         ILOG << "UNK " << gid << ' ' << type << ' ' << tkr << ' ' << tkrName;
    //     }
    // }
    // ILOG << "good " << good << " bad " << bad;

    // return dte;
    return 0;
}

bool HfsTickSourceHH::on_time() {
    sleep(5);
    while (reading_){        
        if (readCount_ - lastCount_ < 50) {
            reading_ = false;
            // fclose(pFile_);
            io_service_.stop();
            cout << readCount_ << endl;
            break;
        }else {
            cout << "speed:" << readCount_ - lastCount_ << endl;
            lastCount_ = readCount_;
        }
        sleep(10);
    }
    // write
    string strHead = "Tkr,Time,Index,Price,Volume,Turnover,BSFlag,OrderKind,FunctionCode,AskOrder,BidOrder\n";
    for (auto iter = transMap.begin(); iter != transMap.end();iter++) {
        char fname[125] = {0};
        sprintf(fname, "../data/2015/%s/%d/Transaction.csv", iter->first.c_str(), dte_);
        cout << fname << endl;
        FILE *pout = fopen(fname, "w+");
        if(!pout){
            ILOG << "file open filed ";
            continue;
        }            
        fwrite(strHead.c_str(), strHead.length(), 1, pout);
        fwrite(iter->second.c_str(), iter->second.length(), 1, pout);
        fclose(pout);
    }
    strHead = "Tkr,Time,Status,PreClose,Open,High,Low,Match,"
              "AskPrice0,AskPrice1,AskPrice2,AskPrice3,AskPrice4,AskPrice5,AskPrice6,AskPrice7,AskPrice8,AskPrice9,"
              "AskVol0,AskVol1,AskVol2,AskVol3,AskVol4,AskVol5,AskVol6,AskVol7,AskVol8,AskVol9,"
              "BidPrice0,BidPrice1,BidPrice2,BidPrice3,BidPrice4,BidPrice5,BidPrice6,BidPrice7,BidPrice8,BidPrice9,"
              "BidVol0,BidVol1,BidVol2,BidVol3,BidVol4,BidVol5,BidVol6,BidVol7,BidVol8,BidVol9,"
              "NumTrades,Volume,Turnover,TotalBidVol,TotalAskVol,WeightedAvgBidPrice,WeightedAvgAskPrice,IOPV,YieldToMaturity,HighLimited,LowLimited\n";
    for (auto iter = mktMap.begin(); iter != mktMap.end();iter++) {
        char fname[125] = {0};
        sprintf(fname, "../data/2015/%s/%d/TickAB.csv", iter->first.c_str(), dte_);
        cout << fname << endl;
        FILE *pout = fopen(fname, "w+");
        if(!pout){
            ILOG << "file open filed ";
            continue;
        }         
        fwrite(strHead.c_str(), strHead.length(), 1, pout);
        fwrite(iter->second.c_str(), iter->second.length(), 1, pout);
        fclose(pout);
    }
    strHead = "Tkr,Time,Side,Price,Orders,ABItems,ABVolume\n";
    for (auto iter = odqMap.begin(); iter != odqMap.end();iter++) {
        char fname[125] = {0};
        sprintf(fname, "../data/2015/%s/%d/OrderQueue.csv", iter->first.c_str(), dte_);
        cout << fname << endl;
        FILE *pout = fopen(fname, "w+");
        if(!pout){
            ILOG << "file open filed ";
            continue;
        } 
        fwrite(strHead.c_str(), strHead.length(), 1, pout);
        fwrite(iter->second.c_str(), iter->second.length(), 1, pout);
        fclose(pout);
    }
    strHead = "Tkr,Time,Index,Price,Volume,Type,BSFlag\n";
    for (auto iter = odMap.begin(); iter != odMap.end();iter++) {
        char fname[125] = {0};
        sprintf(fname, "../data/2015/%s/%d/Order.csv", iter->first.c_str(), dte_);
        cout << fname << endl;
        FILE *pout = fopen(fname, "w+");
        if(!pout){
            ILOG << "file open filed ";
            continue;
        } 
        fwrite(strHead.c_str(), strHead.length(), 1, pout);
        fwrite(iter->second.c_str(), iter->second.length(), 1, pout);
        fclose(pout);
    }
    cout << "quit" << endl;
    return true;
}
bool HfsTickSourceHH::run() {
    hfs_msg_head_t head;
    char *buf = &msgBuf_[0];
    size_t sz = 0;
    reading_ = true;

    for(;reading_;) {
        try {
            sz = boost::asio::read(socket_, boost::asio::buffer(&head, sizeof(hfs_msg_head_t)));
            assert(sz == sizeof(hfs_msg_head_t));
            sz = boost::asio::read(socket_, boost::asio::buffer(buf, head.nDataLen));
            assert((int)sz == head.nDataLen);
        }
        catch(std::exception &ex) {
            FLOG << "读取实时数据时遇到异常，连接中断：" << ex.what();
            reading_ = false;
            return false;
            for(;;) {
                try {
                    socket_.close();

                    boost::asio::socket_base::reuse_address option(true);
                    socket_.set_option(option);
                }
                catch(std::exception &e) {
                    FLOG << e.what();
                }

                FLOG << "准备在3秒后重连宏汇数据源！...";
                boost::this_thread::sleep(boost::posix_time::seconds(3));
                if(login(1)) break;
            }
            continue;
        }

        readCount_++;
        // fwrite(&head, sizeof(hfs_msg_head_t), 1, pFile_);
        // fwrite(buf, sizeof(char), head.nDataLen, pFile_);
        switch(head.sDataType) {
        case ID_TDFTELE_MARKETDATA:
            process_market_data(&head, buf);
            break;
        case ID_TDFTELE_ORDERQUEUE:
            //process_order_queue(&head, buf);
            break;
        case ID_TDFTELE_ADDCODE:
            //process_addcode(&head, buf);
            break;
        case ID_TDFTELE_ORDER:
            //process_order(&head, buf);
            break;
        case ID_TDFTELE_TRANSACTIONEX:
            //process_transactionex(&head, buf);
            break;
        case ID_TDFTELE_INDEXDATA:
            //process_index(&head, buf);
            break;
        case ID_TDFTELE_MARKETDATA_FUTURES:
            process_market_data_futures(&head, buf);
            break;
        default:
            break;
        }
    }
    ILOG << "数据源读取结束！";

    return true;
}

int HfsTickSourceHH::process_market_data(hfs_msg_head_t *head, char *data, hfs_quote_src_t src) {
    // fwrite(head, sizeof(hfs_msg_head_t), 1, pFile_);
    // fwrite(data, sizeof(char), head->nDataLen, pFile_);
    int N = *(int *)data;
    for(int i=0;i<N;i++) {
        hfs_market_data_t *md = ((hfs_market_data_t *)(data+sizeof(int))) + i;
        int gid = md->gid;
        auto iter = vgids_.find(gid);
        if (iter == vgids_.end())
            continue;
        char buf[512] = {0};
        // tkr, time, status,preclose,open,high,low,match,askprice,askvol,bidprice, bidvol,numtrades,vol,turnover,totalbidvol,totalaskvol,weightedavgbidprice, weightedavgaskprice,iopv,nYieldToMaturity,nHighLimited,nLowLimited,chPrefix
        sprintf(buf, "%s,%d,%d,%d,%d,%d,%d,%d,"
                     "%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,"
                     "%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,"
                     "%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,"
                     "%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,"
                     "%d,%lld,%lld,%lld,%lld,%d,%d,%d,%d,%d,%d\n",
                iter->second.c_str(), md->nTime, md->nStatus, md->nPreClose, md->nOpen, md->nHigh, md->nLow, md->nMatch,
                md->nAskPrice[0], md->nAskPrice[1], md->nAskPrice[2], md->nAskPrice[3], md->nAskPrice[4], md->nAskPrice[5], md->nAskPrice[6], md->nAskPrice[7], md->nAskPrice[8], md->nAskPrice[9],
                md->nAskVol[0], md->nAskVol[1], md->nAskVol[2], md->nAskVol[3], md->nAskVol[4], md->nAskVol[5], md->nAskVol[6], md->nAskVol[7], md->nAskVol[8], md->nAskVol[9],
                md->nBidPrice[0], md->nBidPrice[1], md->nBidPrice[2], md->nBidPrice[3], md->nBidPrice[4], md->nBidPrice[5], md->nBidPrice[6], md->nBidPrice[7], md->nBidPrice[8], md->nBidPrice[9],
                md->nBidVol[0], md->nBidVol[1], md->nBidVol[2], md->nBidVol[3], md->nBidVol[4], md->nBidVol[5], md->nBidVol[6], md->nBidVol[7], md->nBidVol[8], md->nBidVol[9],
                md->nNumTrades, md->iVolume, md->iTurnover, md->nTotalBidVol, md->nTotalAskVol, md->nWeightedAvgBidPrice, md->nWeightedAvgAskPrice, 
                md->nIOPV, md->nYieldToMaturity, md->nHighLimited, md->nLowLimited);
        auto iter2 = mktMap.find(iter->second);
        if (iter2 == mktMap.end()) {
            mktMap.insert(make_pair(iter->second, buf));
        } else {
            iter2->second += string(buf);
        }
        // if (mktMap2.find(iter->second) == mktMap.end()) {
        //     vector<string> tmp(4 * 60 * 20);
        //     tmp.push_back(buf);
        //     mktMap2.insert(make_pair(iter->second, tmp));
        // } else {
        //     mktMap2[iter->second].push_back(string(buf));
        // }
        // const SecuCode *sc = HfsSecuTable::get_mutable_instance().getSCByGid(gid);
        // if(!sc || sc->idnum <= 0) return 0;

        // hfs_tick_t tick;
        // tick.gid = md->gid;
        // tick.idnum = sc->idnum;
        // tick.updTime = hhmmssxxx_to_ms(md->nTime);
        // tick.updType = UPD_MARKETDATA;
        // tick.updOrder = ++ValidTickCount_;
        // tick.srcType = src;
        // memcpy(&tick.md, md, sizeof(hfs_market_data_t));

        // on_tick(tick);
    }

    return 0;
}

int HfsTickSourceHH::process_market_data_futures(hfs_msg_head_t *head, char *data, hfs_quote_src_t src) {
    // int N = *(int *)data;
    // for(int i=0;i<N;i++) {
    //     hfs_market_data_futures_t *md = ((hfs_market_data_futures_t *)(data+sizeof(int))) + i;
    //     int gid = md->gid;
    //     const SecuCode *sc = HfsSecuTable::get_mutable_instance().getSCByGid(gid);
    //     if(!sc || sc->idnum <= 0) return 0;

    //     hfs_tick_t tick;
    //     tick.gid      = md->gid;
    //     tick.idnum    = sc->idnum;
    //     tick.updTime  = hhmmssxxx_to_ms(md->nTime);
    //     tick.updType  = UPD_MARKETDATA_FUTURES;
    //     tick.updOrder = ++ValidTickCount;
    //     tick.srcType  = src;
    //     memcpy(&tick.mdf, md, sizeof(hfs_market_data_futures_t));

    //     on_tick(tick);
    // }

    return 0;
}
int HfsTickSourceHH::process_transactionex(hfs_msg_head_t *head, char *data, hfs_quote_src_t src) {
    hfs_transactionex_head_t *thead = (hfs_transactionex_head_t *)data;
    int gid = thead->gid;
    if (vgids_.find(gid) == vgids_.end())
    {
        cout << "get other tkrs data " << gid <<endl;
        return 0;
    }
        
    for(int i=0;i<thead->nItems;i++) {
        hfs_transactionex_t *ts = ((hfs_transactionex_t *)(data+sizeof(hfs_transactionex_head_t))) + i;
        char buf[512] = {0};
        // time, index,price,vol,turnover,bsflag,orderkind,functioncode,askorder,bidorder
        sprintf(buf, "%s,%d,%d,%d,%d,%d,%c,%c,%c,%d,%d\n",
                vgids_[gid].c_str(), ts->nTime, ts->nIndex, ts->nPrice, ts->nVolume, ts->nTurnover, 
                ts->chBSFlag=='\0'?' ':ts->chBSFlag, ts->chOrderKind=='\0'?' ':ts->chOrderKind,
                ts->chFunctionCode=='\0'?' ':ts->chFunctionCode, 
                ts->nAskOrder, ts->nBidOrder);
        auto iter = transMap.find(vgids_[gid]);
        if (iter == transMap.end()) {
            transMap.insert(make_pair(vgids_[gid], buf));
        } else {
            transMap[vgids_[gid]] += string(buf);
        }
    }
    return 0;
}
int HfsTickSourceHH::process_transaction(hfs_msg_head_t *head, char *data, hfs_quote_src_t src) {
    hfs_transaction_head_t *thead = (hfs_transaction_head_t *)data;
    int gid = thead->gid;
    if (vgids_.find(gid) == vgids_.end())
        return 0;
    // const SecuCode *sc = HfsSecuTable::get_mutable_instance().getSCByGid(gid);
    // if(!sc || sc->idnum <= 0) return 0;

    // for(int i=0;i<thead->nItems;i++) {
    //     hfs_transaction_t *ts = ((hfs_transaction_t *)(data+sizeof(hfs_transaction_head_t))) + i;
        //     hfs_tick_t tick;
        //     tick.gid = gid;
        //     tick.idnum = sc->idnum;
        //     tick.updTime = hhmmssxxx_to_ms(ts->nTime);
        //     tick.updType = UPD_TRANSACTION;
        //     tick.updOrder = ++ValidTickCount;
        //     tick.srcType = src;
        //     memcpy(&tick.ts, ts, sizeof(hfs_transaction_t));

        //     on_tick(tick);
    // }

    return 0;
}

int HfsTickSourceHH::process_index(hfs_msg_head_t *head, char *data, hfs_quote_src_t src) {
    // hfs_index_t *indx = (hfs_index_t *)data;
    // int gid = indx->gid;
    // const SecuCode *sc = HfsSecuTable::get_mutable_instance().getSCByGid(gid);
    // if(!sc) return 0;

    // hfs_tick_t tick;
    // tick.gid = gid;
    // tick.idnum = sc->idnum;
    // tick.updTime = hhmmssxxx_to_ms(indx->nTime);
    // tick.updType = UPD_INDEX;
    // tick.updOrder = ++ValidTickCount;
    // tick.srcType = src;
    // memcpy(&tick.ts, indx, sizeof(hfs_index_t));

    // on_tick(tick);

    return 0;
}

int HfsTickSourceHH::process_order_queue(hfs_msg_head_t *head, char *data, hfs_quote_src_t src) {
    TDFDefine_OrderQueueHead *oqhead = (TDFDefine_OrderQueueHead *)data;
    int n = oqhead->nItems;
    for (int i = 0; i < n;i++) {
        hfs_order_queue_t *odq = ((hfs_order_queue_t*)(data+sizeof(TDFDefine_OrderQueueHead))) + i;
        int gid = odq->gid;
        if (vgids_.find(gid) == vgids_.end())
        {
            //cout << "get other tkrs data " << gid <<endl;
            continue;
        }
        //memset(&odq->nABVolume[odq->nABItems], 0, sizeof(int) * (200 - odq->nABItems));
        char tmp[6] = {0};
        string vols = "";
        for (int j = 0; j < odq->nABItems;j++) {
            sprintf(tmp, "%d|", odq->nABVolume[j]);
            vols += string(tmp);
        }
        char buf[1024] = {0};
        // tkr, time,side,price,orders,abitems,abvol
        sprintf(buf, "%s,%d,%c,%d,%d,%d,%s\n",
                vgids_[gid].c_str(), odq->nTime, odq->nSide, odq->nPrice, odq->nOrders, odq->nABItems, vols.c_str());
        // sprintf(buf, "%s,%d,%c,%d,%d,%d,"
        //              "%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d\n",
        //         vgids_[gid].c_str(), odq->nTime, odq->nSide, odq->nPrice, odq->nOrders, odq->nABItems,
        //         odq->nABVolume[0], odq->nABVolume[1], odq->nABVolume[2], odq->nABVolume[3], odq->nABVolume[4],
        //         odq->nABVolume[5], odq->nABVolume[6], odq->nABVolume[7], odq->nABVolume[8], odq->nABVolume[9],
        //         odq->nABVolume[10], odq->nABVolume[11], odq->nABVolume[12], odq->nABVolume[13], odq->nABVolume[14],
        //         odq->nABVolume[15], odq->nABVolume[16], odq->nABVolume[17], odq->nABVolume[18], odq->nABVolume[19] );
        auto iter = odqMap.find(vgids_[gid]);
        if (iter == odqMap.end()) {
            odqMap.insert(make_pair(vgids_[gid], buf));
        } else {
            odqMap[vgids_[gid]] += string(buf);
        }
    }
    return 0;
}

int HfsTickSourceHH::process_addcode(hfs_msg_head_t *head, char *data, hfs_quote_src_t src) {
    return 0;
}

int HfsTickSourceHH::process_order(hfs_msg_head_t *head, char *data, hfs_quote_src_t src) {
    TDFDefine_OrderHead *ohead = (TDFDefine_OrderHead *)data;
    int gid = ohead->gid;
    if (vgids_.find(gid) == vgids_.end())
        return 0;
    for (int i = 0; i < ohead->nItems;i++) {
        TDFDefine_Order *od = ((TDFDefine_Order *)(data + sizeof(TDFDefine_OrderHead))) + i;
        char buf[512] = {0};
        // tkr, time, index, price, vol, type, bsflag
        sprintf(buf, "%s,%d,%d,%d,%d,%c,%c\n",
                vgids_[gid].c_str(), od->nTime, od->nIndex, od->nPrice, od->nVolume, od->chType, od->chBSFlag=='\0'?' ':od->chBSFlag);
        if (odMap.find(vgids_[gid]) == odMap.end()) {
            odMap.insert(make_pair(vgids_[gid], buf));
        } else {
            odMap[vgids_[gid]] += string(buf);
        }
    }
    return 0;
}
bool HfsTickSourceHH::on_bmo(){
    return login();
}

bool HfsTickSourceHH::on_amc() {
    return true;
}
