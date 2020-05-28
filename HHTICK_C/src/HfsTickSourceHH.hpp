#pragma once

#include "HfsTick.hpp"
#include <boost/asio.hpp>
#include <boost/function.hpp>
#include <boost/shared_ptr.hpp>
#include <vector>
#include <unordered_map>

class HfsTickSourceHH
{
  public:
    virtual bool on_bmo();
    virtual bool run();
    virtual bool on_amc();
    bool on_time();

  public:
    HfsTickSourceHH(boost::asio::io_service &io, int dte);
    bool loadConfig(const char* configFile);
    virtual ~HfsTickSourceHH();

  private: 
    bool login(int mode = 1);    //mode=0,,处理码表；否则不处理 0 接受实时行情， 1 接收历史行情
    int process_code_table(hfs_msg_head_t *head, char *data); //返回当前日期
    int process_market_data(hfs_msg_head_t *head, char *data, hfs_quote_src_t src = DTYPE_SHL2);
    int process_market_data_L1(hfs_msg_head_t *head, char *data, hfs_quote_src_t src = DTYPE_SHL2);
    int process_market_data_futures(hfs_msg_head_t *head, char *data, hfs_quote_src_t src = DTYPE_SHL2);
    int process_transaction(hfs_msg_head_t *head, char *data, hfs_quote_src_t src = DTYPE_SHL2);
    int process_index(hfs_msg_head_t *head, char *data, hfs_quote_src_t src = DTYPE_SHL2);
    int process_order(hfs_msg_head_t *head, char *data, hfs_quote_src_t src = DTYPE_SHL2);
    int process_order_queue(hfs_msg_head_t *head, char *data, hfs_quote_src_t src = DTYPE_SHL2);
    int process_addcode(hfs_msg_head_t *head, char *data, hfs_quote_src_t src = DTYPE_SHL2);
    int process_transactionex(hfs_msg_head_t *head, char *data, hfs_quote_src_t src = DTYPE_SHL2);
    int loop_read(boost::asio::ip::tcp::socket *psocket_, hfs_quote_src_t src = DTYPE_SHL2);

  private:
    vector<char> msgBuf_;

    int ValidTickCount_;

    int readCount_, readStamp_, lastCount_;
    int curTime_;

    hfs_quote_src_t srcType_;
    bool reading_;
    boost::asio::io_service &io_service_;
    boost::asio::ip::tcp::socket socket_;
    int dte_;
    FILE *pFile_;
    string address_;
    string port_;
    string user_;
    string passwd_ ;
    string exch_ ;
    string exchFlag_ ;
    string tkrs_;
    vector<string> vtkrs_;
    unordered_map<int, string> vgids_;

    unordered_map<string, string> transMap;
    unordered_map<string, string> mktMap;
    unordered_map<string, string> odqMap;
    unordered_map<string, string> odMap;

    unordered_map<string, vector<string>> transMap2;
    unordered_map<string, vector<string>> mktMap2;
    unordered_map<string, vector<string>> odqMap2;
    unordered_map<string, vector<string>> odMap2;
};
