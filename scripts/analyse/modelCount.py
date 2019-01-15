from joblib import Parallel, delayed
import types
import copy_reg
import multiprocessing
import numpy
import subprocess
import copy
import re
import random
import sys
import time
import math
import os
from pyparsing import nestedExpr
import filecmp
import itertools
from reduceMap import simplifyCNF
maxMHash=32
core=16
structDir='/playpen/ziqiao/2project/klee/analyzer/linux/'
Kleaver="kleaver -use-cex-cache --use-forked-solver"
def pause():
    programPause = raw_input("Press the <ENTER> key to continue...")
def createHashFile(i,pcfile,val,attackerVal,lock,it):
    hashfile= structDir+'hash_'+str(i)+'.pc'
    print hashfile
    tryAgain=True
    while tryAgain:
        try:

            lock.acquire()
            f=open(structDir+'hash_'+str(i)+'.pc')
            read=f.read();
            allline0=read.split('\n')
            f.close()
            lock.release()
            tryAgain=False
        except:
            print 'try again for'+hashfile
    outpath=pcfile+'.hash_'+str(i)
    allline=[]
    pair=[val-1,val+1]
    for line in allline0:
            line=line.replace("UPPERBOUND",str(pair[1])).replace("LOWERBOUND",str(pair[0])).replace("ALPHA",str(val)).replace("KEYVAL",str(random.getrandbits(64))).replace("ATTACKERVAL",str(attackerVal))
            allline.append(line)
    of=open(outpath,'w+')
    of.write('\n'.join(allline));
    of.close()
    return outpath


def solve(pcfile):
    runcommand=Kleaver+' -evaluate '+pcfile
    result=subprocess.check_output(runcommand,stderr=subprocess.STDOUT,shell=True)
    if result.find('INVALID')>0:
        example={}
        constraints=[]
        lines=result.split('\n')
        for line in lines:
            line=line.replace(', ',',')
            tokens=line.split()
            if len(tokens)>0 and tokens[0]=='Array':
                #print tokens
                assign=tokens[2]
                start=assign.find('[')
                end=assign.find(']')
                sym=assign[:start]
                if sym=='y':
                    constraints=""
                    valstr=assign[start+1:end]
                    vals=valstr.split(',')
                    #print vals
                    constraints='true'
                    final=0
                    for i in range(0,len(vals)):
                        constraints='(And '+constraints+' (Eq '+str(vals[i])+' (ReadLSB w8 '+str(i)+' '+sym+')))'
                        final=final+int(int(vals[i])*math.pow(2,8*i))
                    #print final
                    constraints=' (Eq false '+constraints+')'
                    #print constraints
                    #constraints=' (Eq false (Eq '+str(final)+' (ReadLSB w32 0 '+sym+')))'
                    return [final,constraints] 
        return 'UNSAT'
    elif result.find('VALID')>0:
        return 'UNSAT'
    else:
        return 'ERROR'

def weight(y):
    if type(y) is list:
        return len(y)
    return 1
				
def BSAT0(pcfile,pivot,r,wmax,S):
    wmin=wmax/r
    wtotal=0
    Y=[]
    newpcfile=pcfile
    while wtotal/(wmin*r)<=pivot:
        result=solve(pcfile)
        if result=='UNSAT' or result=='ERROR':
            break
        y=result[0]
        addBlock=result[1]
        Y.append(y)
        f=open(pcfile)
        read=f.read()
        f.close()
        index=read.find(']',read.find('query'))
        read=read[:index]+'\n'+addBlock+read[index:]
        f=open(pcfile,'w')
        f.write(read)
        f.close()
        w=weight(y)
        wtotal=wtotal+w
        wmin=min(wmin,w)
    print len(Y)
    return [Y,wmin*r]
def BSAT(pcfile,pivot,r,wmax,S):
    runcommand="kleaver -evaluate-bound -bound="+str(pivot+1)+' '+pcfile
    result=subprocess.check_output(runcommand,stderr=subprocess.STDOUT,shell=True)
    lines=result.split('\n')
    for line in lines:
        pair=line.split(':')
        if pair[0]=='COUNT':
            count=int(pair[1])
            break;
    return [count,r]
def BSAT2(pcfile,pivot,r,wmax,S):
    f=open(pcfile)
    read=f.read()
    f.close()
    declare=[]
    lst=read.split('\n')
    syms=[]
    for line in lst:
        if line.startswith('array'):
            declare.append(line)
            one=line.split()
            sym=one[1]
            sym=sym[:sym.find('[')]
            syms.append(sym)
    falseindex=read.rfind('false')
    endquery=read.rfind(']',0,falseindex)
    startquery=read.find('[',read.find('(query'))+1
    query=read[startquery:endquery]
    end=read[endquery:]
    newdeclareis=[]
    newqueries=[]
    diff=[]
    nsym=len(syms)
    finalpcfile= pcfile+'tmp'

    command=Kleaver+' -evaluate-and -out='+pcfile+'tmp'
    for i in range(0,pivot+1):
        newquery=query
        newdeclare=[]
        for k in range(0,nsym):
            line=declare[k]
            newline=line.replace('[',str(i)+'[')
            newdeclare.append(newline)
            #newquery=re.sub(r'\b'+syms[k]+'\b',syms[k]+str(i),newquery)
            newquery=newquery.replace(' '+syms[k]+')',' '+syms[k]+str(i)+')').replace(' '+syms[k]+']',' '+syms[k]+str(i)+']').replace('['+syms[k]+']','['+syms[k]+str(i)+']')    
        if i>0:
            new='(Ult (ReadLSB w32 0 y'+str(i)+') (ReadLSB w32 0 y'+str(i-1)+'))'
            diff.append(new)
        newqueries.append(newquery)
        newend=end.replace('[y]','[y'+str(i)+']')
        write='\n'.join(newdeclare)+'\n'+'(query ['+newquery+'\n'+newend 
        newpcfile=pcfile+'tmp'+str(i)
        f=open(newpcfile,'w+')
        f.write(write)
        f.close()
        if i<pivot:
            command=command+' -link-pc-file='+newpcfile
        else:
            command=command+' '+newpcfile
    print command
    subprocess.check_output(command,stderr=subprocess.STDOUT,shell=True)
    runcommand="kleaver -evaluate " +finalpcfile
    result=subprocess.check_output(runcommand,stderr=subprocess.STDOUT,shell=True)
    if result.find('INVALID')>0:
        return [pivot+1,r]
    else:
        BSAT1(pcfile,pivot,r,wmax,S)



def WeightMCCore(pcfile,S,pivot,r,wmax,attackerVal,startmHash,lock,it):
	newpcfile=pcfile+'.tmp'+str(it)
	tryAgain=True

	while(tryAgain):
		try:
			tryAgain=False
                        print 'wait for lock'
                        lock.acquire()

                        print 'got for lock'
			os.system('cp '+pcfile+' '+newpcfile)
                        lock.release()
		except:
			print 'try again'
	'''result=BSAT(newpcfile,pivot, r,wmax,S)
    Y=result[0]
    wmax=result[1]
    wY=weight(Y)
    if wY/wmax<=pivot:
        return [wY,wmax,1]'''
	if False:
		print 'hi'
	else:
		i=startmHash
		while 1:
			print i
			i=i+1
			alpha=int(random.getrandbits(i))
			newhashfile=createHashFile(i,pcfile,alpha,attackerVal,lock,it)
			newpcfile=pcfile+str(it)+'.tmp_'+str(i)
			command=Kleaver+' -evaluate-and -out='+newpcfile+' -link-pc-file='+pcfile+' '+newhashfile
			#command=Kleaver+' -evaluate-and -out='+newpcfile+' '+newhashfile
                        lock.acquire()
			result=subprocess.check_output(command,stderr=subprocess.STDOUT,shell=True)
                        lock.release()
                        print "start BSAT"
			result=BSAT(newpcfile,pivot, r,wmax,S)
			wY=result[0]
			wmax=result[1]
			if (wY/wmax<=pivot and wY>0):
				print "break",i,wY
				break
			if i==maxMHash:
				break
		if wY==0 or wY/wmax>pivot:
			return [-1,wmax,i]
		else:
			return [wY*math.pow(2,i-1)/wmax,wmax,i]
def formatPCfileHash(pcfile):
    f=open(pcfile)
    read=f.read()
    f.close()
    if read.find('array y[4]')<0:
        read='array y[4]: w32 -> w8 = symbolic\n'+read
    if read.find('(Eq (ReadLSB w32 1140 tk) (ReadLSB w32 0 y))')<0:
        querystart=read.find('[',read.find('query'))
        read=read[:querystart+1]+'(Eq (ReadLSB w32 1140 tk) (ReadLSB w32 0 y))\n'+read[querystart+1:]
    resultstart=read.find('[',read.find('false []')+8)+1
    resultend=len(read)-1
    if read[resultstart:resultend].find('y ')<0:
        read=read[:resultstart]+'y '+read[resultstart:]
    f=open(pcfile,'w')
    f.write(read)
    f.close()
import multiprocessing
from functools import partial
def weightMCOnce(pcfile,S,pivot,r,wmax,attackerVal,startmhash,iterative):
    print 'hi'+str(iterative)
    return WeightMCCore(pcfile,S,pivot,r,wmax,attackerVal,startmhash,lock,iterative)
import datetime

def init_child(lock_):
        global lock
        lock = lock_
def WeightMC0(pcfile,attackerVal=100,core=8,epsilon=0.5,sigma=0.2,S=[],r=1):
	count=0
	C=[]
	wmax=1
	formatPCfileHash(pcfile)
	pivot=int(2*math.exp(1.5)*math.pow((1+1/epsilon),2))
	print pivot
	t=35*math.log(3/sigma,2)
	t=int(t)
	print t
	startmHash=26
        lock=multiprocessing.Lock()
	pool = multiprocessing.Pool(processes=core,initializer=init_child, initargs=(lock,))

	func = partial(WeightMCOnce, pcfile,S,pivot,r,wmax,attackerVal,startmHash) 
	#pool.map(func, range(0,t))
	outf=open('result'+str(datetime.datetime.now().time()),'w+')
	for result in pool.imap_unordered(func,range(0,t)):
		c=result[0]
		wmax=result[1]
		startmHash=result[2]-6
		print c, wmax
		if c>=0:
			C.append(c)
			outf.write(str(c)+'\n')
	'''	for counter in range(0,t):
		result=WeightMCCore(pcfile,S,pivot,r,wmax,attackerVal,startmHash,counter)
		#pause()
		c=result[0]
		wmax=result[1]
		startmHash=result[2]-6
		print c, wmax
		if c>=0:
			C.append(c)'''
	finalCount=numpy.median(C)
	outf.close()
	print finalCount
	pool.close()
	pool.join()

def checkInLst(sym,lst):
	for one in lst:
            print one,sym
            if re.match(one,sym,re.DOTALL):
                print 'True'
                return True
	return False

def setIndCNF(cnffile,secretlst,deplst):
    file=open(cnffile)
    content=file.read();
    file.close()
    declares=content[content.find('c array'):].split('\n')
    inds=[]
    deps=[]
    newcontent=""
    for declare in declares:
        declare=re.sub(' +',' ',declare)
        ones=declare.split(' ')
        if len(ones)>3:
            #one[0]=='c'
            symbolindex=ones[1].split('_')
            l=len(symbolindex)
            symbol='_'.join(symbolindex[1:l-1])
            if checkInLst(symbol, secretlst):
                ind=' '.join(ones[2:])
                inds.append(ind)
                newcontent=newcontent+'c ind '+ind+' 0\n'
            elif checkInLst(symbol,deplst):
                dep=' '.join(ones[2:])
                deps.append(dep)
                newcontent=newcontent+'c dep '+dep+' 0\n'

    newcontent=newcontent+content
    file=open(cnffile,'w+')
    file.write(newcontent)
    file.close()


def WeightMC(secretlst,deplst,epsilon,sigma,pcfile):
        #secretlst=['tk[1140]']
        # secretlst=readSecretlst(secretcnf)
	count=0
	C=[]
	wmax=1
	#formatPCfileHash(pcfile)
	pivot=int(2*math.exp(1.5)*math.pow((1+1/epsilon),2))
	print pivot
	#t=35*math.log(3/sigma,2)
	#t=int(t)
	#print t
	smtfile=pcfile+'.smt2'
	command='kleaver --print-smtlib -out='+smtfile+' '+pcfile
	subprocess.check_output(command,stderr=subprocess.STDOUT,shell=True);
	cnfname=pcfile
	cnffile=cnfname+'0.cnf'
	command='stp --output-CNF --out-file='+cnfname+' '+smtfile
	subprocess.check_output(command,stderr=subprocess.STDOUT,shell=True);
	setIndCNF(cnffile,secretlst,deplst)
	#simplifyCNF(cnffile)
	command='scalmc --unset=1 --mode=1  --pivotAC='+str(pivot)+' --threads='+str(core)+' '+cnffile;
	try:
		result=subprocess.check_output(command,stderr=subprocess.STDOUT,shell=True)
	except subprocess.CalledProcessError as grepexc:                                                                                                   
		result=grepexc.output
	keys='Number of solutions is:'
	index=len(keys)+result.find(keys)
	s=result[index:]
	v=re.split('x|\^',s)
	print v
	val=int(v[0])
	base=int(v[1])
	mag=int(v[2])
	return val*math.pow(base,mag);

