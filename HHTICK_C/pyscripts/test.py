import redis
import pdb 
remote_r = redis.Redis('172.18.94.127', port=8080)
locate_r = redis.Redis('192.168.1.16')
while(1):
    #pdb.set_trace()
    d = remote_r.rpop('CATS_REDIS_T0_SIM_INS')
    if d:
        print d
        locate_r.lpush("CATS_REDIS_INS",d)
    d = locate_r.rpop('CATS_REDIS_ORD')
    if d:
        #print d
        #pdb.set_trace()
        remote_r.lpush("CATS_REDIS_T0_SIM_ORD",d)
