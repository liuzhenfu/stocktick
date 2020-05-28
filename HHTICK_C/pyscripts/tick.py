# -*- coding: utf-8 -*-
# @author: LZF
# @date: 2017.10.26


from ctypes import *
import struct
'''
python 定义宏汇数据结构 from HfsTick.hpp
'''
class TDFDefine_MsgHead_(Structure):
    _pack_ = 1
    _fields_ = [('sFlags', c_ushort),
                ('sDataType', c_ushort),
                ('nDataLen', c_int),
                ('nTime', c_int),
                ('nOrder', c_int)]


'''sFlags  sDataType nDataLen nTime nOrder'''
TDFDefine_MsgHead = '<HHiii' 
'''chUserName  chPassword chID chMD5'''
TDFDefine_Login = '<16s32s8s32s'
'''chInfo nAnswer nMarkets chMarketFlag nDynDate '''
TDFDefine_LoginAnswer = '64sii' + '4s' * 32 + 'i' * 32
''' '''
TDFDefine_RequestCodeTable = ''
''' '''
TDFDefine_RequestMarketData = ''
'''合约列表头 nSource nDate nCount nFlags '''
TDFDefine_SecurityCodeHead = '<iiii'
'''合约信息 gid nType chSecurityCode chSymbol '''
TDFDefine_SecurityCode = '<ii8s16s'
'''逐笔成交头 gid nItems '''
TDFDefine_TransactionHead = '<ii'
'''逐笔成交数据 nTime nIndex nPrice nVolume nTurnover '''
TDFDefine_Transaction = '<iiiii'
'''逐笔成交扩展头 gid nItems '''
TDFDefine_TransactionExHead = '<ii'
'''逐笔成交扩展数据 nTime nIndex nPrice nVolume nTurnover chBSflag chOrderKind chFunctionCode chResv nAskOrder nBidOrder'''
TDFDefine_TransactionEx = '<iiiiiccccii'
'''委托头 gid nItems'''
TDFDefine_OrderHead = '<ii'
'''逐笔委托数据 nTime nIndex nPrice nVolume chType chBSFlag chResv'''
TDFDefine_Order = '<' + 'i'*4 + 'c'*2 + '2s'
'''委托队列头 '''
TDFDefine_OrderQueueHead = '<i'
'''委托队列数据 '''
TDFDefine_OrderQueue = '<' + 'i'*7
''' '''
TDFDefine_OrderQueue_FAST = ''
'''行情头 '''
TDFDefine_MarketDataHead = '<i'
'''行情数据 '''
TDFDefine_MarketData = '<' + 'i'*3 + 'I'*5 + 'I'*10 + 'I'*10 + 'I'*10 + 'I'*10 + 'I' + 'q'*4 + 'I'*2 + 'i'*2 + 'I'*2 + '4s'
'''指数头 '''
TDFDefine_IndexDataHead = '<i'
'''指数数据 '''
TDFDefine_IndexData = '<iiiiiiqqi'
''' '''
TDFDefine_SecurityCodeHead = '<iiii'
''' '''
TDFDefine_SecurityCode = '<ii8s16s'


if __name__ == '__main__':
    head = TDFDefine_MsgHead
    print sizeof(head)
