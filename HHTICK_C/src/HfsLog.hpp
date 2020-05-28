#pragma once

#include <boost/log/trivial.hpp>
#include <boost/filesystem.hpp>
#include <string>

#define ILOG  BOOST_LOG_TRIVIAL(info)
#define ELOG  BOOST_LOG_TRIVIAL(error)
#define DLOG  BOOST_LOG_TRIVIAL(debug)
#define WLOG  BOOST_LOG_TRIVIAL(warning)
#define TLOG  BOOST_LOG_TRIVIAL(trace)
#define FLOG  BOOST_LOG_TRIVIAL(fatal)    << __FILE__ << ":" << __FUNCTION__ << ":" << __LINE__ << ":"

#define FUNC_CALL_COUNTER     // Func_Call cc(0, __FUNCTION__);
class Func_Call
{
  public:
    Func_Call(long lcount, const char *pfundname) {
        ltimes = lcount;
        fun_name = pfundname;
        TLOG << fun_name << " enter";
    }
    ~Func_Call() {
        TLOG << fun_name << " leave";
    }

  private:
    long ltimes;
    std::string fun_name;
};
