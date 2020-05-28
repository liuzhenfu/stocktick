#include "HfsTickSourceHH.hpp"
#include "xml_parser.hpp"
#include "HfsLog.hpp"
#include "HfsTickSourceHHApi.hpp"
#include <boost/bind.hpp>
#include <boost/thread.hpp>
#include <boost/lexical_cast.hpp>
#include <boost/algorithm/string.hpp>
#include <ctime>

using namespace boost;
using boost::asio::ip::tcp;
using namespace boost::posix_time;

boost::asio::io_service io_service_;
HfsTickSourceHH *shl2 = NULL;
void io_service_run() {
    boost::asio::io_service::work work(io_service_);
	io_service_.run();
	ILOG << "io_serive_退出！";
}

bool init() {
    try {
		boost::thread io_thread(io_service_run);
        io_thread.detach();
    }
    catch (std::exception &ex){
        FLOG << "init遭遇异常:" << ex.what();
        return false;
    }
}

bool loadConfig(const char* configFile) {
    a2ftool::XmlNode root_node(configFile);
    a2ftool::XmlNode TE_node = root_node.getChild("TradeEngine");
    return true;
}
int today() {
	time_t t;
	struct tm *tmp;
	t = time(NULL);
	tmp = localtime(&t);

	char buf[128];
	strftime(buf, 128, "%Y%m%d", tmp);
	return atoi(buf);
}

void run_socket(const char *configFile,int dte){
    init();
    shl2 = new HfsTickSourceHH(io_service_, dte);
    shl2->loadConfig(configFile);
    if(shl2->on_bmo()) {
        boost::thread t(boost::bind(&HfsTickSourceHH::run, shl2));
        boost::thread t1(boost::bind(&HfsTickSourceHH::on_time, shl2));
        t1.detach();
        t.join();
    }
}

void run_api(const char *configFile,int dte){
    HfsTickSourceHHApi* api = HfsTickSourceHHApi::getInstance();
    api->setDte(dte);
    api->loadConfig(configFile);
    if(api->on_bmo()) {
        api->run();
    } else {
        FLOG << "api connect failed";
    }
}
int main(int argc, char **argv){
    if(argc < 2) {
		FLOG << "usage:" << argv[0] << " configFile";
		return -1;
	}
    const char *configFile = argv[1];
    cout << "configFile:" << configFile << endl;
    int dte = today();
    if(argc > 2) {
        dte = atoi(argv[2]);
    }
    cout << "dte: " << dte << endl;
    run_socket(configFile, dte);
    return 0;
}