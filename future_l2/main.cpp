#include <iostream>
#include <fstream>
#include <string>
#include <string.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <time.h>
#include <stdio.h>
#include <stdlib.h>
#include <iomanip>
#include <map>
#include <vector>
#include <algorithm> 
//#include "csvparser.h"
#include "FileMapper.h"
#include "FuturesInfo.h"
#include "MarketData.h"
#include "XeleMdFtdcUserApiStruct.h"
#include "a2f_time.h"
using namespace std;
using namespace a2ftool;
std::vector<std::string> split(const  std::string& s, const std::string& delim)
{
    std::vector<std::string> elems;
    size_t pos = 0;
    size_t len = s.length();
    size_t delim_len = delim.length();
    if (delim_len == 0) return elems;
    while (pos < len)
    {
        int find_pos = s.find(delim, pos);
        if (find_pos < 0)
        {
            elems.push_back(s.substr(pos, len - pos));
            break;
        }
        elems.push_back(s.substr(pos, find_pos - pos));
        pos = find_pos + delim_len;
    }
    return elems;
}
string get_day_befor(string time)
{
    string buffer ="";
    int months[]={31,28,31,30,31,30,31,31,30,31,30,31};
    std::vector<std::string> tmp = split(time,"-");
    int year = atoi(tmp[0].c_str());
    int month = atoi(tmp[1].c_str());
    int day = atoi(tmp[2].c_str());
    if (year%4 == 0)
    {
        months[1]=29;
    }
    if (day==1){
        if (month==1)
        {
             year--;
             month=12;
             day=31;
        }
        else
        {
            month--;
            day=months[month-1];
        }
    }else
    {
        day--;
    }
    buffer +=std::to_string(year);
    if (month<10)
    {
        buffer +=string("0");
        buffer +=std::to_string(month);
    }
    else
    {
        buffer +=std::to_string(month);
    }
    if (day<10)
    {
        buffer +=string("0");
        buffer +=std::to_string(day);
    }
    else
    {
        buffer +=std::to_string(day);
    }
    return buffer;
}

string del_char(string &src,char ch)
{
	string::iterator   it;
	for (it =src.begin(); it != src.end(); ++it)
	{
		if (*it==ch)
                   src.erase(it);
	}
	return src;
}


bool sort_function(CXeleShfeHighLevelOneMarketData* first,CXeleShfeHighLevelOneMarketData* second)
{
	map<string,map<string,int> > mCont;
    map<string,int> tmp;
    mCont["bu"] = tmp;
    tmp["bu"] = 1;
    mCont["al"] = tmp;
    tmp["al"] = 1;
    mCont["ag"] = tmp;
    tmp["ag"] = 1;
    mCont["zn"] = tmp;
    tmp["zn"] = 1;
    mCont["ru"] = tmp;
    tmp["ru"] = 1;
    mCont["rb"] = tmp;
    tmp["rb"] = 1;
    mCont["ni"] = tmp;
    tmp["ni"] = 1;
    mCont["hc"] = tmp;
    tmp["hc"] = 1;
    mCont["cu"] = tmp;
	map<string,map<string,int> >::iterator it1;
	map<string,map<string,int> >::iterator it2;
	
	string fir = first->UpdateTime;
	string sec = second->UpdateTime;
    string f_Instrument = first->Instrument;
	string s_Instrument = second->Instrument;
	int compare = sec.compare(fir);
	//long second_updatetime= HumanReadableTime(second->UpdateTime).Time2Microsecond();
	if (compare == 0)
	{
		if (first->UpdateMillisec == second->UpdateMillisec)
		{
			/*
        		map<string,map<string,int> >::iterator it;
        		for (it = mCont.begin();it!=mCont.end();++it)
			{
                		cout<<it->first<<"->[";
				map<string ,int>::iterator myit;
				for(myit=it->second.begin();myit!=it->second.end();++myit)
				{
					cout<<myit->first<<",";
				}
				cout<<"]"<<endl;
			}
			*/
			if (f_Instrument.length()<2 || s_Instrument.length()<2)
			{
				return false;
			}
			string f_substr = f_Instrument.substr(0,2);				
			string s_substr = s_Instrument.substr(0,2);				
			it1 = mCont.find(f_substr);
			it2 = mCont.find(s_substr);
			if (f_substr.compare(s_substr)==0)
			{
				return false;
			}
			//cout<<"first:"<<f_Instrument<<"->"<<"second:"<<s_Instrument<<endl;
			//cout<<"first:"<<f_substr<<"->"<<"second:"<<s_substr<<endl;
			if (it1!=mCont.end() && it2!=mCont.end())
			{
				if (it1->second.find(s_substr) != it1->second.end())
				{
					return true;
				}else if(it2->second.find(f_substr) != it2->second.end())
				{
					return false;
				}else
				{
					return false;
				}
			}else if(it1!=mCont.end() && it2==mCont.end())
			{
				return true;
			}else if(it1==mCont.end() && it2!=mCont.end())
			{
				return false;
			}
			else{
				return false;
			}
			
			
		}else
		{
			return (first->UpdateMillisec < second->UpdateMillisec);
		}
	}else if(compare>0)
	{
		return true;
	}else
	{
		return false;
	}
	
}
void Quick_Sort(CXeleShfeHighLevelOneMarketData **array, int Start_Index, int End_Index) {
    if (End_Index >= Start_Index) {
        int first = Start_Index;
        int last = End_Index;
        CXeleShfeHighLevelOneMarketData* key = array[first];
        while (first < last) {
            while (first < last && HumanReadableTime(array[last]->UpdateTime) > HumanReadableTime(key->UpdateTime)) {
                last--;
            }
            array[first] = array[last];
            while (first < last && HumanReadableTime(array[first]->UpdateTime) < HumanReadableTime(key->UpdateTime)) {
                first++;
            }
            while (first < last && HumanReadableTime(array[last]->UpdateTime) == HumanReadableTime(key->UpdateTime)) {
		while (first < last && array[last]->UpdateMillisec >= key->UpdateMillisec) {
			last--;
		}
		while (first < last && array[first]->UpdateMillisec <= key->UpdateMillisec) {
			first++;
		}
            }
            array[last] = array[first];
        }
        array[first] = key;
        Quick_Sort(array, Start_Index, first - 1);
        Quick_Sort(array, first + 1, End_Index);
    }
}

map<string, vector<string>> getfilename(void){
    cout<<"getfilename"<<endl;
    char line[100];
    FILE *fp;
    map<string, vector<string>> result;
    map<string, vector<string>>::iterator it;
    string cmd = "ls -B data/";
    const char *sysCommand = cmd.data();
    if ((fp = popen(sysCommand, "r")) == NULL) {
        cout << "error" << endl;
        return result;
    }
    while (fgets(line, sizeof(line)-1, fp) != NULL){
        string filename = line;
        string date = filename.substr(2,8);
        it = result.find(date);
        if (it!= result.end()) 
        {
            it->second.push_back(filename.substr(0,filename.length()-1));    
        }else
        {
            vector<string> tmp;
            tmp.push_back(filename.substr(0,filename.length()-1));
            result[date] = tmp;
        }   
        //result.push_back(line);
    }
    pclose(fp);
    cout<<"end getfilename"<<endl;
    return result;
}


int main(void)
{
    cout<<sizeof(CXeleShfeHighLevelOneMarketData)<<endl;
    cout<<sizeof(DataHeader)<<endl;
    return 0;
    string befor_night_day="19700101";
    map<string, vector<string>> files = getfilename();
    map<string, vector<string>>::iterator file_it;
    for (file_it =files.begin();file_it!=files.end();++file_it)
    {
        if (file_it->first < "20160613")
        {
            continue;
        }
        cout<<file_it->first<<" -> ";
        std::map<string, std::vector<CXeleShfeHighLevelOneMarketData*>> my_map_day;
        std::map<string, std::vector<CXeleShfeHighLevelOneMarketData*>> my_map_night_first;
        std::map<string, std::vector<CXeleShfeHighLevelOneMarketData*>> my_map_night_second;
        std::map<string, std::vector<CXeleShfeHighLevelOneMarketData*>>::iterator it;
        for(int i=0;i<file_it->second.size();i++)
        {
            cout<<file_it->second[i]<<" ;";
            string filename = "data/"+file_it->second[i];
            ifstream infile(filename);
            string sLine;
            bool head = true;
            while (!infile.eof()) {
                getline(infile, sLine); // Get a line
                if (head)
                {
                    head=false;
                    continue; //跳过文件头
                }
                if (sLine == "")
                    continue;
    	        CXeleShfeHighLevelOneMarketData* pcshd = new CXeleShfeHighLevelOneMarketData();
                //cout<<sLine<<endl;
                std::vector<std::string> tmp = split(sLine,",");
                //cout<<"tmp size:"<<tmp.size()<<endl;
                for (int m =0 ;m<tmp.size();m++)
                {
                    int instrument_len= tmp[26].length()+1;
	                strncpy(pcshd->Instrument, tmp[26].c_str(), instrument_len);
                    int UpdateTime_len=tmp[1].length()+1;
	
	                strncpy(pcshd->UpdateTime, tmp[1].c_str(), UpdateTime_len);
                    //cshd.UpdateTime=time_spilt[1];
                    if (tmp[30].length()>0)
                    {
	                    pcshd->UpdateMillisec=atoi(tmp[30].c_str());
                    }else
                    {
	                    pcshd->UpdateMillisec=0;
                    }
                    if (tmp[41].length()>0)
                    {
	                    pcshd->Volume=atoi(tmp[41].c_str());
                    }else
                    {
	                    pcshd->Volume=0;
                    }
                    if (tmp[27].length()>0)
                    {
	                    pcshd->LastPrice=atof(tmp[27].c_str());
                    }else
                    {
	                    pcshd->LastPrice=0;
                    }
                    if (tmp[38].length()>0)
                    {
	                    pcshd->Turnover=atof(tmp[38].c_str());
                    }else
                    {
	                    pcshd->Turnover=0;
                    }
                    if (tmp[31].length()>0)
                    {
	                    pcshd->OpenInterest=atof(tmp[31].c_str());
                    }else
                    {
	                    pcshd->OpenInterest=0;
                    }
                    if (tmp[13].length()>0)
                    {
	                    pcshd->BidPrice=atof(tmp[13].c_str());
                    }else
                    {
	                    pcshd->BidPrice=0;
                    }
                    if (tmp[2].length()>0)
                    {
	                    pcshd->AskPrice=atof(tmp[2].c_str());
                    }else
                    {
	                    pcshd->AskPrice=0;
                    }
                    if (tmp[18].length()>0)
                    {
	                    pcshd->BidVolume=atoi(tmp[18].c_str());
                    }else
                    {
	                    pcshd->BidVolume=0;
                    }
                    if (tmp[7].length()>0)
                    {
	                    pcshd->AskVolume=atoi(tmp[7].c_str());  
                    }else
                    {
	                    pcshd->AskVolume=atoi(tmp[7].c_str());  
                    }
                }
                /*
                cout <<"Instrument:"<<pcshd->Instrument<<endl;
                cout <<"UpdateTime:"<<pcshd->UpdateTime<<endl;
                cout <<"UpdateMillisec:"<<pcshd->UpdateMillisec<<endl;
                cout <<"Volume:"<<pcshd->Volume<<endl;
                cout <<"LastPrice"<<pcshd->LastPrice<<endl;
                cout <<"Turnover:"<<pcshd->Turnover<<endl;
                cout <<"OpenInterest:"<<pcshd->OpenInterest<<endl;
                cout <<"BidPrice:"<<pcshd->BidPrice<<endl;
                cout <<"AskPrice:"<<pcshd->AskPrice<<endl;
                cout <<"BidVolume:"<<pcshd->BidVolume<<endl;
                cout <<"AskVolume:"<<pcshd->AskVolume<<endl;
                */
                string compare_time = tmp[1];
                string key = tmp[0];
                if ((compare_time.compare("08:30:00")>0) && (compare_time.compare("16:00:00")<0))
                {

		            it = my_map_day.find(key);
		            if (it != my_map_day.end())
        	        {
			            my_map_day.find(key)->second.push_back(pcshd);
		            }
		            else
		            {
	     		        std::vector<CXeleShfeHighLevelOneMarketData*> tmp;
	     		        tmp.push_back(pcshd);
	     		        my_map_day[key]=tmp;
		            }

                }
                //else if ("21:00:00" <= time_spilt[1] && time_spilt[1] <="24:00:00")
                else if ((compare_time.compare("20:30:00")>0) && (compare_time.compare("24:00:00")<0))
                {

		            it = my_map_night_first.find(key);
		            if (it != my_map_night_first.end())
        	        {
			            my_map_night_first.find(key)->second.push_back(pcshd);
		            }
		            else
		            {
	     		        std::vector<CXeleShfeHighLevelOneMarketData*> tmp;
	     		        tmp.push_back(pcshd);
	     		        my_map_night_first[key]=tmp;
		            }

	            }
                else if (compare_time.compare("00:00:00") >=0 && compare_time.compare("04:00:00") <0)
	            {

		            it = my_map_night_second.find(key);
		            if (it != my_map_night_second.end())
        	        {
			            my_map_night_second.find(key)->second.push_back(pcshd);
		            }
		            else
		            {
	     		        std::vector<CXeleShfeHighLevelOneMarketData*> tmp;
	     		        tmp.push_back(pcshd);
	     		        my_map_night_second[key]=tmp;
		            }

	            }else
                {
                    delete pcshd;
                }

                //sleep(1) ;
            }

        }
        for (it=my_map_day.begin(); it!=my_map_day.end(); ++it)
        {
	        cout<<it->first<<"->"<<time(0)<<endl;
	        string outfilename= "out/"+it->first +"-day.dat";
	        FileMapper<CXeleShfeHighLevelOneMarketData,DataHeader> myfile; 
            if(myfile.init(outfilename,false,5*1024*1024))
	        {
		        std::vector<CXeleShfeHighLevelOneMarketData*> tmp = it->second;
		        std::stable_sort(tmp.begin(),tmp.end(),sort_function);
		        myfile.pushData(tmp);
	        }
            else
	        {
		        myfile.init(outfilename,true,5*1024*1024);
		        std::vector<CXeleShfeHighLevelOneMarketData*> tmp = it->second;
		        std::stable_sort(tmp.begin(),tmp.end(),sort_function);
		        myfile.pushData(tmp);
	        }
        
        }
        for (it=my_map_night_first.begin(); it!=my_map_night_first.end(); ++it)
        {
	        string outfilename= "out/" + befor_night_day +"-night.dat";
	        FileMapper<CXeleShfeHighLevelOneMarketData,DataHeader> myfile; 
            if(myfile.init(outfilename,false,5*1024*1024))
	        {
		        std::vector<CXeleShfeHighLevelOneMarketData*> tmp = it->second;
		        std::stable_sort(tmp.begin(),tmp.end(),sort_function);
		        myfile.pushData(tmp);
	        }
	        else
	        {
		        myfile.init(outfilename,true,5*1024*1024);
		        std::vector<CXeleShfeHighLevelOneMarketData*> tmp = it->second;
		        std::stable_sort(tmp.begin(),tmp.end(),sort_function);
		        myfile.pushData(tmp);
	        }
        }
        for (it=my_map_night_second.begin(); it!=my_map_night_second.end(); ++it)
        {
	        string outfilename= "out/" + befor_night_day +"-night.dat";
	        FileMapper<CXeleShfeHighLevelOneMarketData,DataHeader> myfile; 
            if(myfile.init(outfilename,false,5*1024*1024))
	        {
		        std::vector<CXeleShfeHighLevelOneMarketData*> tmp = it->second;
		        std::stable_sort(tmp.begin(),tmp.end(),sort_function);
		        myfile.pushData(tmp);
	        }
	        else
	        {
		        myfile.init(outfilename,true,5*1024*1024);
		        std::vector<CXeleShfeHighLevelOneMarketData*> tmp = it->second;
		        std::stable_sort(tmp.begin(),tmp.end(),sort_function);
		        myfile.pushData(tmp);
	        }
        }
        befor_night_day = file_it ->first;
        
        for (it=my_map_day.begin(); it!=my_map_day.end(); ++it)
        {
            for (int n =0;n<it->second.size();n++)
            {
                delete it->second[n];
            }
        }
        for (it=my_map_night_first.begin(); it!=my_map_night_first.end(); ++it)
        {
            for (int n =0;n<it->second.size();n++)
            {
                delete it->second[n];
            }
        }
        for (it=my_map_night_second.begin(); it!=my_map_night_second.end(); ++it)
        {
            for (int n =0;n<it->second.size();n++)
            {
                delete it->second[n];
            }
        }
    }
    return 0;
}
