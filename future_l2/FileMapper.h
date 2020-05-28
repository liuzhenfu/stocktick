/*************************************************************************
	> File Name: FileHeader.h
	> Author: ma6174
	> Mail: ma6174@163.com
	> Created Time: Fri 24 Feb 2017 06:13:19 PM CST
 ************************************************************************/
#ifndef _FILE_MAPPER_H_
#define _FILE_MAPPER_H_
#include <stdio.h>
#include <stdlib.h>
#include <sys/mman.h>
#include<sys/stat.h>
#include <unistd.h>
#include <fcntl.h>
#include<iostream>
#include <vector>
typedef unsigned int uint32;
typedef int int32;
//#include "Log.h"
using namespace std;
/*struct FileHeader {
    uint32 m_nLength;
    uint32 m_nFileSize;
    char m_sUpdateDate[30];
};*/

template<class DataField, class Header>
class FileMapper {
    Header* m_pHeader;
    DataField* m_pData;
//    uint32 m_nSize;
  public:

    FileMapper(): m_pHeader(0), m_pData(0) {
    }
    bool init(const std::string& filePath, bool clear, size_t reserveSize){
        release();
        int flag;
        mode_t mod;
        int ret = -1;
        if(clear){
            flag = O_RDWR | O_CREAT;
            mod = 00666;
        }else{
            flag = O_RDWR;
            mod = S_IRUSR;
        }
        int f = open(filePath.c_str(), flag, mod);
        if(f < 0){
            //LOG_INFO("failed to open file: {}", filePath.c_str());
            //cout<<"failed to open file: {}"<< filePath.c_str()<<endl;
            m_pHeader = nullptr;
            return false;
        }
        size_t fileSize = reserveSize * (sizeof(DataField));
//        if(clear){
            ret = ftruncate(f, fileSize);
            if(ret < 0){
                std::cerr << "reserveSize:" << reserveSize << std::endl;
                std::cerr << "filesize:" << fileSize << std::endl;
            }
  //      }
        
        char* mapper = (char*) mmap(0, fileSize, PROT_READ | PROT_WRITE, MAP_SHARED, f, 0);
        close(f); 
        if(mapper == 0){
            std::cerr << "map error"<< std::endl;
            return false;
        }
        m_pHeader = (Header*)mapper;
        m_pData = (DataField*)(m_pHeader + 1);
//        m_nSize = m_pHeader->m_nLength;
        if(clear){
            m_pHeader->m_nLength = 0;
            m_pHeader->m_nFileSize = fileSize;
//            msync((void*)mapper, fileSize, MS_ASYNC);
        }
        return true;
    }
    bool load(const std::string& fileName) {
        release();
        int f = open(fileName.c_str(), O_RDONLY, S_IRUSR);
        if(f < 0){
            m_pHeader = nullptr;
            //LOG_INFO("failed to open file: {}", fileName.c_str());
            cout<<"failed to open file: {}"<< fileName.c_str()<<endl;
            return false;
        }
        struct stat stat;
        fstat(f, &stat);
        
        char* mapper = (char*) mmap(0, stat.st_size, PROT_READ, MAP_SHARED, f, 0);
        close(f);
        if(mapper == 0){
            std::cerr << "map error"<< std::endl;
            return false;
        }
        m_pHeader = (Header*)mapper;
        m_pData = (DataField*)(m_pHeader + 1);
//        m_nSize = m_pHeader->m_nLength;
        return true;
    }

    DataField* getData() {
        return m_pData;
    }

    uint32 getIndex() {
        return m_pHeader->m_nLength -1 ;
    }

    char* getUpdateDate(){
        return m_pHeader->m_sUpdateDate;
    }

    void release(){
       if(m_pHeader != nullptr)
            munmap((void *)m_pHeader, m_pHeader->m_nFileSize);
    }
    ~FileMapper() {
        release();
    //    munmap((void *)m_pHeader, fileSize);
    }

    void pushData(vector<DataField*> data) {
        time_t timep;
        time(&timep);
        sprintf(m_pHeader->m_sUpdateDate, "%s", ctime(&timep));

//		m_pHeader->m_sName
//		std::cout << m_pHeader->m_sName << std::endl;
        for(uint32 i = 0; i < data.size(); i ++){
            m_pData[m_pHeader->m_nLength + i] = *(data[i]);
        }
        m_pHeader->m_nLength += data.size();
        msync((void*)m_pHeader, m_pHeader->m_nFileSize, MS_ASYNC);
    }
    void flush(){
        msync((void*)m_pHeader, m_pHeader->m_nFileSize, MS_ASYNC);
    } 
    void setHeader(Header header){
        *m_pHeader = header;
        msync((void*)m_pHeader, m_pHeader->m_nFileSize, MS_ASYNC);
    }

    Header getHeader(){
        return *m_pHeader;
    }
    void pushData(DataField* data) {
        time_t timep;
        time(&timep);
        sprintf(m_pHeader->m_sUpdateDate, "%s", ctime(&timep));
        m_pData[m_pHeader->m_nLength] = *data;
        m_pHeader->m_nLength ++ ;
        msync((void*)m_pHeader, m_pHeader->m_nFileSize, MS_ASYNC);
    }





};
#endif
