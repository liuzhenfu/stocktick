#! /bin/sh
cd ../SZ_N/
for eachfile in `ls -B`
do
 filename=${eachfile%.dat.bz2}
 #tar zcvf shfe$filename.gz $filename.dat
 echo $filename
 #bzip2  $filename.dat 
 bunzip2 $filename.dat.bz2
 #echo 'shfe'$filename'.gz'
 #filehead=`echo $filename | awk -F _ '{print $1 }'`
 #filelast=`echo $filename | awk -F _ '{print $2 }'`
 #echo $filehead-$filelast.data
 #mv $filename.dat $filehead-$filelast.dat
done
