# -*- coding: utf-8 -*- #
import os
import pdb
import sys
import pexpect

host = '172.18.94.223'
user = 'root'
passwd = '123456'

prefix = user+'@'+host+':'
# example : scp_get('/datas/a.txt', './')
def scp_get(remote_path, local_path, passwd):
    cmd = 'scp -C -p {} {} '.format(remote_path,local_path)
    child = pexpect.spawn(cmd)

    index = child.expect(['(?i)password', pexpect.EOF, pexpect.TIMEOUT])
    if (index != 0):
        print('scp connect failed')
        child.close(force=True)
        return
    child.sendline(passwd)
    index = child.expect(['%', 'try again'])
    if index == 1:
        print('passwd error')
        return
    print('scp start...')
    while True:
        process = child.read(150)
        print (process)
        if process.find('100%') != -1:
            print 'scp done'
            break
            

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print 'useage {} srcpath destpath'.format(sys.argv[0])
        exit(1)
    
    srcpath = sys.argv[1]
    destpath = sys.argv[2]
    type = sys.argv[3]
    if type == 'u':
        destpath = prefix+destpath
    else:
        srcpath = prefix + srcpath
    scp_get(srcpath, destpath, passwd)
    

