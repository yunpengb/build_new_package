#!/usr/bin/env python
# -*- coding: utf-8 -*-

################################################################################
# @version               v1
# @date                  2015-10-10
# @author                Yunpeng
# @name         replace 69.bin.lzma on a official package **.tar.gz,modify some file to get a new package contain fileloaderRP1
# @Copyright 2015 Nokia Networks. All rights reserved.
################################################################################

import tarfile
import os,sys
import glob
import shutil
import time,re,linecache,time,zipfile
import subprocess
import shutil
from tqdm import tqdm

def untar(fpath,outdir):
    print ('unzip the tar file %s' % fpath)
    tar = tarfile.open(fpath)
    tar.extractall(path = outdir)
    tar.close()
    
def getrootDir():
    homedir = os.getcwd()
    return homedir

def findagz(path):
    for filename in glob.glob(path + r'\\*.tar.gz'):
        return filename

def copyFileto(sourcefile,targetfile):
    shutil.copy(sourcefile,targetfile)

def checkdirExist(dir):
    a = os.path.exists(dir)
    return a    
    
def checkdir(dir):
    if not checkdirExist(dir):
        os.mkdir(dir)
    else:
        removeFileInFirstDir(dir)

def removeFileInFirstDir(targetDir):
    for file in os.listdir(targetDir):
        targetFile = os.path.join(targetDir,  file)
        if os.path.isfile(targetFile):
            os.remove(targetFile)

def findpath(dir,keywords):
    a = [] 
    temp = ''
    for root,dirs,files in os.walk(dir):
        for filespath in files:
            linec = os.path.join(root,filespath)
            if keywords in linec:
                temp = (os.path.join(root,filespath))
                a.append(temp)
    return a
    
def runcmd(cmd,dir=None):
    p = subprocess.Popen(cmd,
        stdout = subprocess.PIPE,shell=True,cwd=dir)
    p.wait()
    return p.stdout.readlines()
    
def replaceXml(origfile,keywords,pattern,newtext,outPath):
    lines = open(origfile).readlines()
    s = ''
    num = 0
    for line in lines:
        num += 1
        if keywords in line:
            print "replace new checksum info~~"
            pool = linecache.getline(origfile,num)
            s += re.sub(pattern,newtext,pool)
        else:
            s += line
    f = open(outPath,'w')
    f.write(s)
    f.close()
    linecache.clearcache()

def zip_dir(dirname,zipfilename):
    filelist = []
    if os.path.isfile(dirname):
        filelist.append(dirname)
    else :
        for root, dirs, files in os.walk(dirname):
            for name in files:
                filelist.append(os.path.join(root, name))

    zf = zipfile.ZipFile(zipfilename, "w", zipfile.zlib.DEFLATED)
    for tar in filelist:
        arcname = tar[len(dirname):]
        #print arcname
        zf.write(tar,arcname)
    zf.close()    

def maketimestamp():
    timestamp = time.strftime('%Y-%m-%d_%H-%M-%S',time.localtime(time.time()))
    return timestamp
    
    
rootdir = getrootDir()
workdir = rootdir + '\\work'
unzipdir = rootdir + '\\unzip'
toolsdir = rootdir + '\\tools'
cl = 'CreateLAR.exe'
zu = 'zutil.exe'


clfile = toolsdir + '\\'+ cl
zufile = toolsdir + '\\'+ zu
ncl = workdir + '\\'+cl
nzu = workdir + '\\'+zu

# unzip tar.gz to 'unzip' folder
checkdir(workdir)
checkdir(unzipdir)
officialname = findagz(rootdir)
print '@@: Find a tar.gz file: [%s]' % officialname
untar(officialname,unzipdir)
print '@@: Unzip done~'

copyFileto(clfile,ncl)
copyFileto(zufile,nzu)

#copy lar from unzip to work
origlarpath = findpath(unzipdir,'FRM-SW_')[0]
origLarName = origlarpath.split('\\')[-1]
copyFileto(origlarpath,workdir + '\\' + origLarName)
os.remove(origlarpath)

# unzip lar
cmd_all = 'CreateLAR.exe -e ' + origLarName
runcmd(cmd_all,'work')

# replace 69.bin
os.remove('work\\69.bin.lzma')
binpath = '69.bin.lzma'
copyFileto(binpath,workdir + '\\' + '69.bin.lzma')

# build a new lar
os.remove('work\\'+ origLarName)
origxmlpath = findpath(workdir,'.xml')[0]
origxmlname = origxmlpath.split('\\')[-1]
createnewCmd = 'CreateLar.exe ' + origxmlname
runcmd(createnewCmd,'work')

#get 69 checksum info
binsumCmd = 'zutil.exe adler32 '+ '69.bin.lzma'
returns = runcmd(binsumCmd,'work')
print returns
pat = re.compile(r"checksum: \d*")
match1 = pat.search(returns[0])
binChecksum = match1.group().split(' ')[1]

#get lar checksum info
larsumCmd = 'zutil.exe adler32 '+ origLarName
returns = runcmd(larsumCmd,'work')
pat = re.compile(r"(0x([a-z0-9]+))")
match2 = pat.search(returns[0])
att =  match2.group().split('0x')[1]
larChecksum = att.upper()

#rename LAR file name according the Checksum info
newlarpath = re.sub(r"_[A-Z0-9]{8}.LAR","_"+ larChecksum+".LAR",origlarpath)
newlarname = re.sub(r"_[A-Z0-9]{8}.LAR","_"+ larChecksum+".LAR",origLarName)
#print 'new lar:'
#print newlarpath
newlarName = newlarpath.split('\\')[-1]
newlarVersion = re.search(r'\d{6}_[A-Z0-9]*',newlarName).group()
os.rename('work\\'+origLarName,'work\\'+newlarname)
copyFileto('work\\'+newlarname,newlarpath)

# copy FileDirectory.xml to work
fdp = findpath(unzipdir,'FileDirectory.xml')

fdpath = ''
for i in range(2):
    if '.txt' not in fdp[i]:
        fdpath = fdp[i]
#print fdpath

# modify LAR checksum on xml
copyFileto(fdpath,workdir + '\\' + 'FileDirectory.xml')
os.remove(fdpath)
pattern = r'name="FRM-SW_(.*?)">'
newtext = 'name="' + newlarName + '" version="'+ newlarVersion +'">'
out = 'work\\haha1.xml'
replaceXml('work\\FileDirectory.xml','FRM-SW_',pattern,newtext,out)

# modify 69.bin checksum on xml
pattern = r'checksum="(\d*)"'
newtext = 'checksum="' + binChecksum +'"'
out = 'work\\haha2.xml'
replaceXml('work\\haha1.xml','69.bin.lzma',pattern,newtext,out)

copyFileto('work\\haha2.xml',fdpath)

print "Wait for seconds ,create new sw ongoing..."
tim = maketimestamp()
zip_dir('unzip\\','NewSW.zip')
os.rename('work',tim)
shutil.rmtree('unzip')
for i in tqdm(range(100)):
    time.sleep(0.01)
print "Create new sw Done! \n     --END--"









