/*************************************************************************
> File Name: a2f_time.h
> Author: zhangyao
> Mail:
> Created Time: 2017年04月06日 星期四 09时46分12秒
************************************************************************/

#ifndef _A2F_TIME_H
#define _A2F_TIME_H
#include <cstring>
#include <sys/time.h>
#include <ctime>
#include <vector>
#include <cmath>
#include <fstream>
#include <algorithm>
namespace a2ftool {
    inline  std::string& Trim(std::string &s) {
        if(s.empty()) {
            return s;
        }

        s.erase(0, s.find_first_not_of(" "));
        s.erase(s.find_last_not_of(" ") + 1);
        return s;
    }
    inline std::vector<long> GenAllDaysInYear(long year) {

        bool is_leap = (year % 4 == 0 ? (year % 100 == 0 ? (year % 400 == 0 ? true : false) : (true)) : (false));

        // start from Jan 1 of this year
        std::vector<long> day_list;
        day_list.reserve(400);
        long weekday[] = {0, 3, 2, 5, 0, 3, 5, 1, 4, 6, 2, 4};
        long day_of_mon[] = {31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};
        if(is_leap)
            day_of_mon[1] = 29;
        for(int m = 1; m <= 12; ++m) {
            for(int d = 1; d <= day_of_mon[m - 1]; ++d) {
                auto y = year;
                y -= m < 3;
                int dayofweek = (y + y / 4 - y / 100 + y / 400 + weekday[ m - 1] + d) % 7;
                if(dayofweek == 0 || dayofweek == 6)
                    continue;
                day_list.push_back(year * 10000 + m * 100 + d);
            }
        }
        return day_list;
    }

    namespace TimePolicy {
        class Normal;
        class TradingDay;

    }

    template<typename policy = TimePolicy::Normal>
    class Clock {
      public:

        bool IsTradingDay() {
            if(tradingday_list.empty())
                throw("TradingDayList is empty, cannot decide if tradingday.", -1);
            return m_is_trading_day;

        }
      protected:

        std::vector <long> tradingday_list;
        size_t m_trading_day_ind;
        bool m_is_trading_day;
        bool m_is_prev_trading_day;
      public:
        long m_trading_day;
        long m_next_trading_day;
        long m_prev_trading_day;

      public:

        timespec core; // this is the core component
        int year;
        int month;
        int day;
        int wday;
        int yday;
        int hour;
        int min;
        int sec;
        long nanosec;
        long elapse; // store time elapsed during start and
        Clock() {
            m_trading_day_ind = 0;
            clock_gettime(CLOCK_REALTIME, &core);
            SetTimeInfo();

            if(policy::IsTrading()) {
                auto tl1 =  GenAllDaysInYear(timeinfo.tm_year + 1900 - 1);
                auto tl2 =  GenAllDaysInYear(timeinfo.tm_year + 1900);
                auto tl3 =  GenAllDaysInYear(timeinfo.tm_year + 1900 + 1);

                std::move(tl2.begin(), tl2.end(), std::back_inserter(tl1));
                std::move(tl3.begin(), tl3.end(), std::back_inserter(tl1));

                SetTradingDayInfo(tl1);
            }
            SetFromCore();

        }
        Clock(const char *string_time, const char *format) {
            if(policy::IsTrading()){
                std::cout << "Trading Clock must be supplied with tradingday list" << std::endl;
                exit(-1);
            }
            // first make timeinfo back to epoch
            const time_t temp = 0;
            auto temp_tm = localtime(&temp);
            timeinfo = *temp_tm;
            year = month = day = wday = yday = hour = min = sec = nanosec = 0;

            // parse it now
            if(strptime(string_time, format, &timeinfo) == NULL){
                std::cout << std::string("Clock cannot properly parse your time string: ") +
                      string_time + " with format: " + format << std::endl;
                exit(-1);
            }

            core.tv_sec = mktime(&timeinfo);
            core.tv_nsec = 0;
            SetFromCore();
            adjust_last_hour = timeinfo.tm_hour;
            m_trading_day = 0;
            m_next_trading_day = 0;
            m_prev_trading_day = 0;
            m_trading_day_ind = 0;
            m_is_trading_day = false;

        }
        // user might be wishing to use clock to represent a date or time
        Clock(const char *string_time, const char *format, std::vector <long> &list) {

            // first make timeinfo back to epoch
            const time_t temp = 0;
            auto temp_tm = localtime(&temp);
            timeinfo = *temp_tm;
            year = month = day = wday = yday = hour = min = sec = nanosec = 0;

            // parse it now
            if(strptime(string_time, format, &timeinfo) == NULL){
                std::cout << std::string("Clock cannot properly parse your time string: ") +
                      string_time + " with format: " + format<< std::endl;
                exit(-1);
            }
            core.tv_sec = mktime(&timeinfo);
            core.tv_nsec = 0;
            SetTimeInfo();
            adjust_last_hour = timeinfo.tm_hour;
            SetTradingDayInfo(list);
            SetFromCore();
        }

        // user might be wishing to use clock to represent a date or time
        Clock(const char *string_time, const char *format, const char* filename) {

            // first make timeinfo back to epoch
            const time_t temp = 0;
            auto temp_tm = localtime(&temp);
            timeinfo = *temp_tm;
            year = month = day = wday = yday = hour = min = sec = nanosec = 0;

            // parse it now
            if(strptime(string_time, format, &timeinfo) == NULL){
                std::cout << std::string("Clock cannot properly parse your time string: ") +
                      string_time + " with format: " + format << std::endl;
                exit(-1);
            }
            core.tv_sec = mktime(&timeinfo);
            core.tv_nsec = 0;
            SetTimeInfo();
            adjust_last_hour = timeinfo.tm_hour;
            SetTradingDayInfo(filename);
            SetFromCore();
        }



        virtual ~Clock() {  }
//! set trading day list
        void SetTradingDayInfo(const std::vector <long> &tl) {
            tradingday_list = tl;
            auto todayInt = DateToIntReal();
            auto yesterdayInt = PrevDateToIntReal();
/*            if(tl.empty())
                throw("Clock does not accept empty trading day list", -1);
            if(tradingday_list[0] > todayInt)
                throw("TradingList not includes today", -1);
            else if(tradingday_list[tradingday_list.size() - 1] < todayInt)
                throw("TradingList not includes today", -1);*/

            for(unsigned int i = 0; i < tradingday_list.size(); ++i) {
                if(tradingday_list[i] >= todayInt) {
                    m_trading_day_ind = i;
                    m_trading_day = tradingday_list[i];
                    if(i < tradingday_list.size() - 1)
                        m_next_trading_day = tradingday_list[i + 1];
                    if(i > 0)
                        m_prev_trading_day = tradingday_list[i - 1];

                    // whether today is trading day?
                    if(tradingday_list[i] == todayInt)
                        m_is_trading_day = true;
                    else
                        m_is_trading_day = false;

                    // whether yesterday is a tradingday?
                    if(tradingday_list[i - 1] == yesterdayInt)
                        m_is_prev_trading_day = true;
                    else
                        m_is_prev_trading_day = false;
                    return;

                }

            }

        }
//! set trading day list
        void SetTradingDayInfo(const std::string filename) {
            std::vector<long> tl;
            std::ifstream IF;
            IF.open(filename.c_str());
            if(!IF.is_open())
                throw("cannot open info file" + filename, -3);

            // parse info file
            std::string line;
            getline(IF, line);
            while(getline(IF, line)) {
                tl.push_back(atoi(line.c_str()));
            }
            IF.close();
            SetTradingDayInfo(tl);
        }

//! set clock from epoch time long
        Clock &Set(time_t epoch_time = 0) {
            memset(&core, 0, sizeof(timespec));
            core.tv_sec = epoch_time;
            auto temp_tm = localtime(&core.tv_sec);
            timeinfo = *temp_tm;
            SetFromCore();
            return *this;
        }

//! equals Set(0)
        Clock &Reset() {
            Set(0);
            return *this;
        }

        Clock &Update(const char *string_time, const char *format) {
            // first make timeinfo back to epoch
            time_t temp = 0;
            auto temp_tm = localtime(&temp);
            timeinfo = *temp_tm;
            year = month = day = wday = yday = hour = min = sec = nanosec = 0;

            // parse it now
            if(strptime(string_time, format, &timeinfo) == NULL)
                throw(std::string("Clock cannot properly parse your time string: ") +
                      string_time + " with format: " + format, -1);
            core.tv_sec = mktime(&timeinfo);
            core.tv_nsec = 0;
            SetFromCore();
        }

//! update time and date
        Clock& Update() {
            clock_gettime(CLOCK_REALTIME, &core);
            SetFromCore();
            return *this;
        }

//! just update time
        Clock& UpdateTime() {
            clock_gettime(CLOCK_REALTIME, &core);
            SetTimeInfo();
            policy::Normalize(DateToIntReal(), m_trading_day, m_next_trading_day, m_prev_trading_day, m_trading_day_ind,
                              m_is_trading_day, m_is_prev_trading_day, core.tv_sec, timeinfo, tradingtimeinfo, tradingday_list);

            //auto temp_tm = localtime (&core.tv_sec);
            //timeinfo = *temp_tm;
            policy::FillTime(timeinfo, tradingtimeinfo, hour, min, sec);
            nanosec = core.tv_nsec;
            return *this;
        }

        std::string Print(const char* format = NULL) {
            return policy::Print(timeinfo, tradingtimeinfo, format);

        }

        long DateToIntReal() {
            return (timeinfo.tm_year + 1900) * 10000 + (timeinfo.tm_mon + 1) * 100 + timeinfo.tm_mday;

        }

        long PrevDateToIntReal() {
            time_t now = time(NULL);
            now = now - (24 * 60 * 60);
            struct tm *t = localtime(&now);
            return (t->tm_year + 1900) * 10000 + (t->tm_mon + 1) * 100 + t->tm_mday;

        }

        long DateToInt() {
            return year * 10000 + month * 100 + day;

        }

        long TimeToInt() {
            return hour * 10000 * 1000 + min * 100 * 1000 + sec * 1000 + int(nanosec / (1000.0 * 1000));

        }

        long Time2Microsecond(){
            return hour*3600l*1000l*1000 + min * 60 * 1000l * 1000 + sec * 1000l * 1000 + nanosec/1000;
        }
        
        long Time2Second(){
            return hour*3600l + min * 60 + sec;
        }
      
        long TimeToIntNormalize() {
            long t = hour * 10000 * 1000 + min * 100 * 1000 + sec * 1000;
            auto millisec = nanosec / (1000.0 * 1000);
            if(millisec < 500)
                t += 0;
            else if(millisec >= 500)
                t += 500;
            return t;

        }

        long TradingTimeToInt() {
            if(DateToIntReal() == m_trading_day)      // now is in trading day
                return TimeToInt();
            else {
                if(PrevDateToIntReal() == m_prev_trading_day && hour < 6)
                    return TimeToInt();
                else
                    return TimeToInt() * -1;

            }

        }

        std::string YearToStr() const {
            char timebuf[10];
            snprintf(timebuf, 5, "%04d", year);
            return std::string(timebuf);

        }

        std::string MonthToStr() const {
            char timebuf[10];
            snprintf(timebuf, 3, "%02d", month);
            return std::string(timebuf);

        }

        std::string DayToStr() const {
            char timebuf[10];
            snprintf(timebuf, 3, "%02d", day);
            return std::string(timebuf);

        }

        std::string HourToStr() const {
            char timebuf[10];
            snprintf(timebuf, 3, "%02d", hour);
            return std::string(timebuf);

        }

        std::string MinuteToStr() const {
            char timebuf[10];
            snprintf(timebuf, 3, "%02d", min);
            return std::string(timebuf);

        }

        std::string SecondToStr() const {
            char timebuf[10];
            snprintf(timebuf, 3, "%02d", sec);
            return std::string(timebuf);

        }

        std::string MillisecondToStr() const {
            char timebuf[10];
            //std::cout<<round( core.tv_nsec/1000/1000   )<<std::endl;
            snprintf(timebuf, 4, "%03d", (int)round(core.tv_nsec / 1000 / 1000));

            return std::string(timebuf);

        }
        class Clock operator + (const int64_t interval) {
            Clock ret = *this;
            ret.core.tv_sec += (int64_t)floor(interval / 1000);
            //ret.core.tv_nsec += (interval - 1000 * (int)floor(interval/1000))*1000;
            ret.core.tv_nsec += (interval - 1000 * (int64_t)floor(interval / 1000)) * 1000 * 1000;
            if(ret.core.tv_nsec >= 1000 * 1000 * 1000) {
                ret.core.tv_sec += 1;
                ret.core.tv_nsec -= 1000 * 1000 * 1000;
            }
            nanosec = ret.core.tv_nsec;
            //std::cout<<interval<<std::endl;
            //std::cout<<1000*(int64_t)floor(interval/1000)<<std::endl;
            //std::cout<<( interval - 1000*(int64_t)floor(interval/1000)  )<<std::endl;
            //std::cout<<ret.core.tv_sec<<" "<<ret.core.tv_nsec<<std::endl;
            auto temp_tm = localtime(&ret.core.tv_sec);
            ret.timeinfo = *temp_tm;

            ret.year = ret.timeinfo.tm_year + 1900;
            ret.month = ret.timeinfo.tm_mon + 1;
            ret.day = ret.timeinfo.tm_mday;
            ret.wday = ret.timeinfo.tm_wday;
            ret.yday = ret.timeinfo.tm_yday;
            ret.hour = ret.timeinfo.tm_hour;
            ret.min = ret.timeinfo.tm_min;
            ret.sec = ret.timeinfo.tm_sec;
            return ret;
        }

        class Clock operator += (const int64_t interval) {
            core.tv_sec += (int64_t)floor(interval / 1000);
            //ret.core.tv_nsec += (interval - 1000 * (int)floor(interval/1000))*1000;
            nanosec += (interval - 1000 * (int64_t)floor(interval / 1000)) * 1000 * 1000;
            if(nanosec >= 1000 * 1000 * 1000) {
                core.tv_sec += 1;
                nanosec -= 1000 * 1000 * 1000;
            }
            core.tv_nsec = nanosec;
            //std::cout<<interval<<std::endl;
            //std::cout<<1000*(int64_t)floor(interval/1000)<<std::endl;
            //std::cout<<( interval - 1000*(int64_t)floor(interval/1000)  )<<std::endl;
            //std::cout<<ret.core.tv_sec<<" "<<ret.core.tv_nsec<<std::endl;
            auto temp_tm = localtime(&core.tv_sec);
            timeinfo = *temp_tm;
            year = timeinfo.tm_year + 1900;
            month = timeinfo.tm_mon + 1;
            day = timeinfo.tm_mday;
            wday = timeinfo.tm_wday;
            yday = timeinfo.tm_yday;
            hour = timeinfo.tm_hour;
            min = timeinfo.tm_min;
            sec = timeinfo.tm_sec;
            return *this;
        }
        class Clock operator - (const int64_t interval) {
            Clock ret = *this;
            ret.core.tv_sec -= (int64_t)floor(interval / 1000);
            int64_t nano = (interval - 1000 * (int64_t)floor(interval / 1000)) * 1000 * 1000;
            if(ret.core.tv_nsec < nano) {
                ret.core.tv_sec -= 1; // borrow 1 sec
                ret.core.tv_nsec = ret.core.tv_nsec + 1000 * 1000 * 1000 - nano;

            } else
                ret.core.tv_nsec -= nano;
            ret.nanosec = ret.core.tv_nsec;

            auto temp_tm = localtime(&ret.core.tv_sec);
            ret.timeinfo = *temp_tm;
            ret.year = ret.timeinfo.tm_year + 1900;
            ret.month = ret.timeinfo.tm_mon + 1;
            ret.day = ret.timeinfo.tm_mday;
            ret.wday = ret.timeinfo.tm_wday;
            ret.yday = ret.timeinfo.tm_yday;
            ret.hour = ret.timeinfo.tm_hour;
            ret.min = ret.timeinfo.tm_min;
            ret.sec = ret.timeinfo.tm_sec;
            return ret;

        }

        class Clock operator -= (const int64_t interval) {

            core.tv_sec -= (int64_t)floor(interval / 1000);
            int64_t nano = (interval - 1000 * (int64_t)floor(interval / 1000)) * 1000 * 1000;
            if(core.tv_nsec < nano) {
                core.tv_sec -= 1; // borrow 1 sec
                core.tv_nsec = core.tv_nsec + 1000 * 1000 * 1000 - nano;

            } else
                core.tv_nsec -= nano;
            nanosec = core.tv_nsec;

            auto temp_tm = localtime(&core.tv_sec);
            timeinfo = *temp_tm;
            year = timeinfo.tm_year + 1900;
            month = timeinfo.tm_mon + 1;
            day = timeinfo.tm_mday;
            wday = timeinfo.tm_wday;
            yday = timeinfo.tm_yday;
            hour = timeinfo.tm_hour;
            min = timeinfo.tm_min;
            sec = timeinfo.tm_sec;
            return *this;

        }



        bool operator < (const Clock& right) {
            if(core.tv_sec == right.core.tv_sec)
                return (core.tv_nsec < right.core.tv_nsec);
            else
                return core.tv_sec < right.core.tv_sec;

        }

        bool operator == (const Clock& right) {
            return (core.tv_sec == right.core.tv_sec) && (core.tv_nsec == right.core.tv_nsec);

        }

        bool operator != (const Clock& right) {
            return !(this->operator==(right));

        }

        bool operator > (const Clock& right) {
            return !(this->operator==(right)) && !(this->operator<(right)) ;

        }

        bool operator >= (const Clock& right) {
            return  !(this->operator<(right)) ;

        }

        bool operator <= (const Clock& right) {
            return  !(this->operator>(right)) ;

        }
      private: //! do not recommend using timeinfo since we have wrapped it
        void SetTimeInfo() {
            auto temp_tm = localtime(&core.tv_sec);
            timeinfo = *temp_tm;

        }
        void SetFromCore() {

            SetTimeInfo();
           // AdjustTradingDay();
          //  policy::Normalize(DateToIntReal(), m_trading_day, m_next_trading_day, m_prev_trading_day, m_trading_day_ind,
//                              m_is_trading_day, m_is_prev_trading_day, core.tv_sec, timeinfo, tradingtimeinfo, tradingday_list);

            policy::Fill(timeinfo, tradingtimeinfo, year, month, day, wday, yday, hour, min, sec);
            nanosec = core.tv_nsec;

        }
        long adjust_last_hour;
        long adjust_last_date;
        void AdjustTradingDay() {

            if(tradingday_list.empty()) {
                if(policy::IsTrading())
                    throw("TradingDay Clock cannot have empty tradingday list", -1);
                else
                    return;

            }
            //if ( timeinfo.tm_hour < adjust_last_hour  ) {
            // get today's real date as integer
            long todayInt = DateToIntReal();
            auto yesterdayInt = PrevDateToIntReal();

            // check tradingday_list boundary
            if(tradingday_list[0] > todayInt)
                throw("TradingList not includes today", -1);
            else if(tradingday_list[tradingday_list.size() - 1] < todayInt)
                throw("TradingList not includes today", -1);

            //for ( unsigned int trading_ind = 0; i<tradingday_list.size(); ++i  )
            // found trading_ind with tradingday_list[trading_ind] >= todayInt
            while(tradingday_list[m_trading_day_ind] > todayInt) {
                --m_trading_day_ind;
            }
            while(tradingday_list[m_trading_day_ind] < todayInt) {
                ++m_trading_day_ind;
            }

            m_trading_day = tradingday_list[m_trading_day_ind];
            auto next_ind = m_trading_day_ind > tradingday_list.size() - 2 ? tradingday_list.size() - 1  : m_trading_day_ind + 1;
            m_next_trading_day = tradingday_list[next_ind];
            auto prev_ind = m_trading_day_ind > 0 ? m_trading_day_ind - 1 : 0;
            m_prev_trading_day = tradingday_list[prev_ind];
            if(tradingday_list[m_trading_day_ind] == todayInt)
                m_is_trading_day = true;
            else
                m_is_trading_day = false;

            if(tradingday_list[m_trading_day_ind - 1] == yesterdayInt)
                m_is_prev_trading_day = true;
            else
                m_is_prev_trading_day = false;

            //throw "";
            //}
            return ;
        }

      protected:
        struct tm timeinfo;
        struct tm tradingtimeinfo;
    };
    namespace TimePolicy {
        class Normal {

          public:
            static bool IsTrading() {
                return false;
            }

            static void Normalize(long real, long& trading, long& next_trading, long& prev_trading,
                                  const size_t trading_ind, bool& is_trading_day, bool& is_prev_trading_day, time_t& sec,
                                  struct tm& timeinfo, struct tm& tradetimeinfo, std::vector<long>& trading_list)
            {}

            static void Fill(struct tm& timeinfo, struct tm& tradetimeinfo,
                             int& year, int& month, int& day, int& wday, int& yday, int& hour, int& min, int& sec) {
                year = timeinfo.tm_year + 1900;
                month = timeinfo.tm_mon + 1;
                day = timeinfo.tm_mday;
                wday = timeinfo.tm_wday;
                yday = timeinfo.tm_yday;
                hour = timeinfo.tm_hour;
                min = timeinfo.tm_min;
                sec = timeinfo.tm_sec;

            }
            static void FillTime(struct tm& timeinfo, struct tm& tradetimeinfo,
                                 int& hour, int& min, int& sec) {
                hour = timeinfo.tm_hour;
                min = timeinfo.tm_min;
                sec = timeinfo.tm_sec;

            }

            static std::string Print(struct tm & timeinfo, struct tm& tradingtimeinfo, const char* format = NULL) {
                char buf[80];
                if(format)
                    strftime(buf, 80, format, &timeinfo);
                else
                    strcpy(buf, asctime(&timeinfo));
                return std::string(buf);

            }


        };
        class TradingDay {
          public:
            static bool IsTrading() {
                return true;
            }

            static void Normalize(long real, long& trading, long& next_trading, long& prev_trading,
                                  const size_t trading_ind, bool& is_trading_day, bool is_prev_trading_day, time_t& sec,
                                  struct tm& timeinfo, struct tm& tradetimeinfo, std::vector<long>& trading_list) {
                const time_t temp = 0;
                struct tm temp_tm, temp_tm2; //temp_tm3;
                temp_tm  = *(localtime(&temp));
                temp_tm2 = *(localtime(&temp));
                // temp_tm3 = *(localtime(&sec));
                // parse it now
                strptime(std::to_string((long long)real).c_str(), "%Y%m%d", &temp_tm);
                strptime(std::to_string((long long)trading).c_str(), "%Y%m%d", &temp_tm2);
                // timeinfo = temp_tm3;
                // throw;
                auto sec2 = sec + mktime(&temp_tm2) - mktime(&temp_tm);
                //std::cout<<real<<" "<<trading<<" "<<mktime(&temp_tm2)<<" "<<mktime(&temp_tm)<<" "<<sec<<" "<<sec2<<std::endl;
                tradetimeinfo = *(localtime(&sec2));

                //! handle special situations in non-trading days
                if(!is_trading_day) {
                    if(is_prev_trading_day  && tradetimeinfo.tm_hour < 6)
                        tradetimeinfo.tm_hour = tradetimeinfo.tm_hour;
                    else
                        tradetimeinfo.tm_hour = -1;
                    return ;
                }

                //! come back to trading days
                if(tradetimeinfo.tm_hour < 6)
                    tradetimeinfo.tm_hour += 24;
                else if(tradetimeinfo.tm_hour < 24 && tradetimeinfo.tm_hour >= 18) {
                    //if ( real == trading  )
                    //{
                    if(is_trading_day) {
                        prev_trading = trading_list[trading_ind];
                        trading = trading_list[trading_ind + 1];
                        next_trading = trading_list[trading_ind + 2];
                    }
                    //}
                    strptime(std::to_string((long long)trading).c_str(), "%Y%m%d", &temp_tm2);
                    // std::cout<<sec<<" "<<real<<" "<<trading<<" "<<next_trading<<" "<<trading<<" "<<prev_trading<<" "<<mktime(&temp_tm2) - mktime(&temp_tm)<<std::endl;
                    sec2 = sec + mktime(&temp_tm2) - mktime(&temp_tm);

                    tradetimeinfo = *(localtime(&sec2));
                }
                // throw "";
            }
            static void Fill(struct tm& timeinfo, struct tm& tradetimeinfo,
                             int& year, int& month, int& day, int& wday, int& yday, int& hour, int& min, int& sec) {
                year = tradetimeinfo.tm_year + 1900;
                month = tradetimeinfo.tm_mon + 1;
                day = tradetimeinfo.tm_mday;
                wday = tradetimeinfo.tm_wday;
                yday = tradetimeinfo.tm_yday;
                hour = tradetimeinfo.tm_hour;

                min = tradetimeinfo.tm_min;
                sec = tradetimeinfo.tm_sec;

            }

            static void FillTime(struct tm& timeinfo, struct tm& tradetimeinfo,
                                 int& hour, int& min, int& sec) {
                hour = tradetimeinfo.tm_hour;
                min = tradetimeinfo.tm_min;
                sec = tradetimeinfo.tm_sec;

            }

            static std::string Print(struct tm & timeinfo, struct tm& tradingtimeinfo, const char* format = NULL) {
                char buf[80];
                if(format)
                    strftime(buf, 80, format, &tradingtimeinfo);
                else
                    strcpy(buf, asctime(&tradingtimeinfo));
                return std::string(buf);

            }

        };
    }
    inline Clock<> HumanReadableTime(const std::string literal) {
        // passed in string literal example:
        // 12:30
        // 1:39:30
        // 1:39:29.300
        // 1:39:19 am (AM, a.m. A.M.)

        std::string hour = "0";
        std::string min = "00";
        std::string sec = "00";
        std::string ms = "000";
        bool is_pm = false;

        std::string time_string = literal.c_str();
        std::transform(time_string.begin(), time_string.end(), time_string.begin(), ::tolower);
        std::string time;
        // Check if there is any AM/am/A.M./a.m./A.M/a.m/
        auto found1 = time_string.find("am");
        auto found2 = time_string.find("a.m");
        auto found3 = time_string.find("pm");
        auto found4 = time_string.find("p.m");

        size_t found;

        if(found1 != std::string::npos)
            time = time_string.substr(0, found1);
        else if(found2 != std::string::npos)
            time = time_string.substr(0, found2);
        else if(found3 != std::string::npos) {
            time = time_string.substr(0, found3);
            is_pm = true;
        } else if(found4 != std::string::npos) {
            time = time_string.substr(0, found4);
            is_pm = true;
        } else
            time = time_string;


        // get first ":"
        found = time.find(":");
        if(found == std::string::npos){
            std::cout << "HumanReadableTime cannot recognize your time string: " + literal << std::endl;
            exit(-1);
        //    throw("HumanReadableTime cannot recognize your time string: " + literal, -1);
        }
        hour = time.substr(0, found);
        if(atoi(hour.c_str()) > 12 && is_pm){
            std::cout << "HumanReadableTime finds your time string: " + literal + " to be illegal" << std::endl;
            exit(-1);
//            throw("HumanReadableTime finds your time string: " + literal + " to be illegal", -1);
        }
       
        if(is_pm)
            hour = std::to_string((long long)(atoi(hour.c_str()) + 12));
        found2 = time.find(":", found + 1);
        if(found2 != std::string::npos) {
            min = time.substr(found + 1, found2 - found - 1);
            found3 = time.find(".", found2 + 1);
            if(found3 != std::string::npos) {
                sec = time.substr(found2 + 1, found3 - found2 - 1);

                ms = time.substr(found3 + 1, time.size() - found3 - 1);
            } else
                sec = time.substr(found2 + 1, time.size() - found2 - 1);
        } else
            min =  time.substr(found + 1, time.size() - found - 1).c_str();

        if(atoi(min.c_str()) >= 60){
            std::cout << "HumanReadableTime illegal time: minute larger than 60" << std::endl;
            exit(-1);
        }
        if(atoi(sec.c_str()) >= 60){
            std::cout << "HumanReadableTime illegal time: second larger than 60" << std::endl;
            exit(-1);
        }
        if(atoi(ms.c_str()) >= 1000){
            std::cout << "HumanReadableTime illegal time: microsecond larger than 1000" << std::endl;
            exit(-1);
           
        }

        auto lit = a2ftool::Trim(hour) + ":" + a2ftool::Trim(min) + ":" + a2ftool::Trim(sec);
        auto clock = Clock<>(lit.c_str(), "%H:%M:%S");
        clock.nanosec = atoi(ms.c_str()) * 1000 * 1000;
        clock.core.tv_nsec = clock.nanosec;
        return clock;


    }
};
#endif
