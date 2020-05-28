source /etc/profile
cd /home/operation/HHTICK_C/pyscripts
echo $(pwd)

nohup /usr/bin/python getTkrsData.py 1>"./stdout.log" 2>"./stderr.log" &