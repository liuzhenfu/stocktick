TARGET = HHTick
OBJECTS = $(patsubst %.cpp, %.o, $(wildcard *.cpp)) 
CPPFLAGS+= -O3 -Wall -std=c++0x -I ..  -I /usr/local/include -DTT_64BIT -DTTEXCEPT -DBOOST_LOG_DYN_LINK -I../include 
LDFLAGS+= -lboost_thread -lboost_log -lboost_serialization -lboost_regex -lboost_program_options -lboost_system -lboost_filesystem -L/usr/local/lib -L../lib -lTDFAPI_v2.7

all: ${OBJECTS}
	echo ${OBJECTS}
	g++ ${OBJECTS} -o ../bin/${TARGET} $(CPPFLAGS) $(LDFLAGS)

.PHONY: clean
clean:
	rm -f ${OBJECTS} ../bin/${TARGET}