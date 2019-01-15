from optparse import OptionParser
import random;
import os;
import re;
import sys;
def getConcern(concernfile):
    f=open(concernfile)
    result=[]
    for line in f:
        line=line.replace('\n','')
        if len(line)>0:
            result.append(line)
    f.close()
    print result
    return result 

def match(check,patterns):
    for pattern in patterns:
        if re.match(pattern,check,re.DOTALL):
            #print 'True',pattern,check
            return True
    #print 'False'
    return False


def getInd(concerns,namefile):
    f=open(namefile)
    name_map={}
    inds=[]
    for line in f:
        line=line.replace('\n','')
        s=line.split(' ')
        #print s[1]
        name=s[1]
        if '__newvar' in name:
            continue
        index=int(name[name.rfind('_')+1:])
        name_map[index]=(s[1],s[2:])
    for index in sorted(name_map.keys()):
        s=name_map[index]
        if match(s[0],concerns):
            if "array_output" in s[0]:
                inds.append(s[1][0])
            else:
                inds=inds+s[1]
    f.close()
    return ' '.join(inds)


def setInd(cnffile,namefile,concernfile,jaccardfile=''):
    indstr=''
    jacstr=''
    pre='ind_'
    concerns=getConcern(concernfile)
    ind=getInd(concerns,namefile)
    if(len(jaccardfile)):
        jaccards=getConcern(jaccardfile)
        jac=getInd(jaccards,namefile)
        jacstr=jacstr+'c jac '+jac+' 0\n'
        pre=pre+'jac_'
    indstr='c ind '+ind+' 0\n'
    f=open(cnffile)
    f2=open(pre+cnffile,'w+')
    f2.write(indstr+jacstr+f.read());
    f2.close()
    f.close()

def setInd2(cnffile,namefile,concernfile,jaccardfile,jaccardfile2=''):
    indstr=''
    jacstr=''
    pre='ind_'
    concerns=getConcern(concernfile)
    ind=getInd(concerns,namefile)
    indstr='c ind '+ind+' 0\n'
    if(len(jaccardfile)):
        jaccards=getConcern(jaccardfile)
        jac=getInd(jaccards,namefile)
        jacstr=jacstr+'c jac '+jac+' 0\n'
        pre=pre+'jac2_'
        jaccard2=getConcern(jaccardfile2)
        jac2=getInd(jaccard2,namefile)
        jacstr=jacstr+'c jac2 '+jac2+' 0\n'

    
    f=open(cnffile)
    f2=open(pre+cnffile,'w+')
    f2.write(indstr+jacstr+f.read());
    f2.close()
    f.close()

def setAttackOb(cnffile,namefile,jaccardfile,attackfile,obfile):
    indstr=''
    jacstr=''
    pre='jac_'
    concerns=getConcern(jaccardfile)
    jac=getInd(concerns,namefile)
    jacstr='c jac '+jac+' 0\n'
    if(len(attackfile)):
        jaccards=getConcern(attackfile)
        jac=getInd(jaccards,namefile)
        jacstr=jacstr+'c attack '+jac+' 0\n'
        pre=pre+'attack_'
    if(len(obfile)):
        jaccards=getConcern(obfile)
        jac=getInd(jaccards,namefile)
        jacstr=jacstr+'c ob '+jac+' 0\n'
        pre=pre+'ob_'

    f=open(cnffile)
    f2=open(pre+cnffile,'w+')
    f2.write(jacstr+f.read());
    f2.close()
    f.close()

def fixSomeInd(cnffile,namefile,concernfile,fixedfile,jaccardfile,some):
    indstr=''
    jacstr=''
    pre='fix_ind_'
    concerns=getConcern(concernfile)
    ind=getInd(concerns,namefile)

    fixs=getInd(getConcern(fixedfile),namefile)
    fixedarr=fixs.split(" ")
    fixed=[]
    constraints=""
    if(len(jaccardfile)):
        jaccards=getConcern(jaccardfile)
        jac=getInd(jaccards,namefile)
        jacstr='c jac '+jac+' 0\n'
        pre=pre+'jac_'
    indstr='c ind '+ind+' 0\n'
    indarr=indstr.split(" ")
    size=len(fixedarr)
    for i in range(0,size/8):
        pos=0
        choice=random.sample(range(0,8),some)
        for var in fixedarr[i*8:(i+1)*8]:
            if pos in choice:
                fixed.append(var)
                if random.getrandbits(1):
                    constraints=constraints+var+' 0\n'
                else:
                    constraints=constraints+"-"+var+' 0\n'
            pos=pos+1
    print constraints
    f=open(cnffile)
    allread=f.read();
    f.close()
    for var in fixed:
        indarr.remove(var)
    indstr=' '.join(indarr)
    f2=open(pre+cnffile,'w+')
    f2.write(indstr+jacstr+allread+constraints);
    f2.close()
def fixSomeIndOpt(option, opt, value, parser):
    argv=parser.rargs
    fixSomeInd(argv[0],argv[1],argv[2],argv[3],argv[4],int(argv[5]))

def setInd2Opt(option, opt, value, parser):
    argv=parser.rargs
    setInd2(argv[0],argv[1],argv[2],argv[3],argv[4])

parser = OptionParser()
parser.add_option("-f",help="-f cnffile namefile indfile fixedfile jaccardfile fixdnum(fixnum out of 8 bits  will be fixed)", action="callback", callback=fixSomeIndOpt)

parser.add_option("-x",help="-x namefile concern indfile ind2file", action="callback", callback=setInd2Opt)
(options, args) = parser.parse_args()
if len(sys.argv)>3:
    if len(sys.argv)==5:
        setInd(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4])
    elif  len(sys.argv)==4:
        setInd(sys.argv[1],sys.argv[2],sys.argv[3])
    elif len(sys.argv)==6:
        setAttackOb(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5])
