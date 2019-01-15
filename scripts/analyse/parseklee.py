import sys
import math
import os
from pyparsing import nestedExpr
class Parser:
    symbol_type={}
    linuxfolder=""
    pathDir=''
    starters=['Eq','Ne','Ult','Ule','Ugt','Uge','Slt','Sle','Sgt','Sge']
    logic={'And':[2,3], 'Or':[2,3], 'Xor':[2,3], 'Shl':[2], 'LShr':[2], 'AShr':[2]}
    readKey=['ReadLSB','Read','ReadMSB']
    structs={}
    readKeys=['ReadLSB','Read','ReadMSB']
    typewidths=[64,32,16,8]
    def is_int(self,s):
        try: 
            int(str(s))
            return True
        except ValueError:
            return False

    def loadDef(self,def_name):
        def_file=open(def_name);
        def_type={}
        for line in def_file:
            lst = line.split(":")
            def_type[lst[0]]=lst[1]
        def_file.close()
        return def_type

    def loadStruct(self,struct):
        structname=struct.strip("struct").strip(" ").strip("\n");
        f=open(structname+".struct");
        elements={}
        for line in f:
            line=line.split();
            offset=int(line[0])
            if not elements.has_key(offset):
                elements[offset]=[]
            elements[offset].append((line[1],line[2]));
        f.close()
        return elements

    def isBranch(self,one):
        for key in self.starters:
            if one.startswith("['"+key+"'"):
                return True
        return False
    def isQuery(self,one):
        return one.startswith("['"+'query'+"'")
    def isLogic(self,one):
        for key in self.logic.keys():
            if str(one).startswith("['"+key+"'"):
                return key
        return ""

    def isRead(self,one):
        for key in self.readKeys:
            if str(one).startswith("['"+key+"'"):
                return True
        return False
                
    def findIndex(self,val,sortedlst):
        index=len(sortedlst)/2
        step=len(sortedlst)/2
        check=sortedlst[index]
        while not val==check:
            if val<sortedlst[index]:
                step=int(step/2)
                index=index-step
                check=sortedlst[index]
                if  step==1:
                    return index
            else:
                step=int(step/2)
                index=index+step
                check=sortedlst[index]
                if step==1 and not val==check:
                    return index-1
        return index

    def findPrefix(self,prefix,new):
        newprefix=[]
        for index in range(0,len(prefix)):
            if not prefix[index]==new[index]:
                break;
            newprefix.append(prefix[index])
        return newprefix

    def findDiff(self,prefix,old):
        diff=[]
        return old[len(prefix):]


    def convertOffset2Field(self,one):
        if self.isRead(one):
            readwidth=int(one[1][1:])
            readoffset=one[2]
            readobj=one[3]
            allname=[]
            if self.symbol_type.has_key(str(readobj)):
                symbol=str(readobj)
                stype=self.symbol_type[symbol]
                if not self.structs.has_key(stype):
                    self.structs[stype]=self.loadStruct(stype);
                structdic=self.structs[stype]
                offsets=structdic.keys()
                offsets.sort();
                readoffset=int(readoffset)*8
                cindex=self.findIndex(readoffset,offsets)
                #print stype,offsets,readoffset,cindex
                sindex=0
                while cindex+sindex<len(offsets) and (int(offsets[cindex+sindex])-int(offsets[cindex])<readwidth):
                    index=cindex+sindex
                    offset=offsets[index]
                    name_type=structdic[offset];
                    names=[]
                    simplename=[]
                    prefix=name_type[0][0].split('.')
                    for candidate in name_type:
                        name=candidate[0].split('.')
                        prefix=self.findPrefix(prefix,name)
                        names.append(name)
                    for nameset in names:
                        nameset=self.findDiff(prefix,nameset)
                        namestr='.'.join(list(nameset))
                        simplename.append(namestr)
                    namestr=symbol+'->'+'('+'.'.join(prefix)+')'+'/'.join(simplename)
                    allname.append(namestr);
                    sindex=sindex+1
                one=[','.join(allname)]
        return one


    def convertDec2Hex(self,one):
        key=self.isLogic(one)
        if not key=="":
            for pos in self.logic[key]:
                if len(one)>pos:
                    if self.is_int(one[pos]):
                        one[pos]=str(hex(int(one[pos])))
        return one
    def printNested(self,of,nest,isPrint=True,convert2Field=False):
        for index in range(0,len(nest)):
            one=nest[index]
            alreadyOne=False
            if isinstance(one,list):
                for oneone in one:
                    if isinstance(oneone,list) and not alreadyOne:
                        alreadyOne=True
                        one=self.printNested(of,one,isPrint,convert2Field)
            one=self.convertDec2Hex(one)
            if convert2Field:
                one=self.convertOffset2Field(one)
            nest[index]=one
        if isPrint and self.isQuery(str(nest)):
            for one in nest:
                of.write(str(one)+'\n')
        return nest

    def parsePC(self,path_str):
        start=path_str.find('(query')
        path_str=path_str[start:];
        path_str=path_str.replace("\n","")
        result=nestedExpr(opener='(',closer=')').parseString(path_str).asList()
        return result



    def parsePath(self,pathfile,symbolfile,linuxfolder):
        pathf=open(pathfile);
        pathc=pathf.read();
        whole=pathc;
        outfile=pathfile.replace('.pc','.pc.new')
        exprfile=pathfile.replace('.pc','.pc.expr')
        print outfile,exprfile
        of=open(outfile,'w+')
        exprof=open(exprfile,'w+')
        exprs=self.parsePC(whole)
        of.write(str(exprs))
       # print exprs
        exprs=self.printNested(exprof,exprs,True,False)
        of.close();
        exprof.close()

    def parseAll(self):
        for pathfile in os.listdir(self.pathDir):
            if pathfile.endswith(".pc"):
                self.parsePath(self.pathDir+'/'+pathfile,self.symbolfile,self.linuxfolder);

    def __init__(self,pathDir0,symbolfile0,linuxfolder0):
        self.pathDir=pathDir0
        self.symbolfile=symbolfile0
        self.symbol_type=self.loadDef(self.symbolfile)
        self.linuxfolder=linuxfolder0

    def parseOb(self,obpath):
        obfile=open(obpath)
        outpath=obpath.replace('.observable','.ob')
        of=open(outpath,'w+')
        allline=[]
        for line in obfile:
            allline.append(line)
        count={}
        assignment={}
        index=1
        while index <len(allline):
            line=allline[index]
            while line.count('(')>line.count(')'):
                index=index+1
                line=line+" "+allline[index]
            pair=line.split(': ')
            index=index+1
            if count.has_key(pair[0]):
                count[pair[0]]=count[pair[0]]+1
            else:
                count[pair[0]]=0
            key=pair[0]+str(count[pair[0]])
            #print pair[1]
            path_str=pair[1].replace('\n',' ')
            exprs=nestedExpr(opener='(',closer=')').parseString(path_str).asList()
            result=self.printNested(of,exprs,False,True)
            assignment[key]=result
            of.write(key+":"+str(result)+"\n")
        obfile.close()
        of.close()
    def parseResult(self):
        for pathfile in os.listdir(self.pathDir):
            if pathfile.endswith(".observable"):
                self.parseOb(self.pathDir+'/'+pathfile)

    def formatOne(self,path):
        f=open(path)
        of=open(path.replace('.pc','.pc0'),'w+')
        of.write(f.read().replace(' -> ',' => ').replace("->",".").replace(' => ',' -> '))
        f.close()
        of.close()

#format .pc to  readable format
    def formatAll(self):
        for pathfile in os.listdir(self.pathDir):
            if pathfile.endswith(".pc"):
                self.formatOne(self.pathDir+'/'+pathfile)
if len(sys.argv)>0:
    parse=Parser("/playpen/ziqiao/2project/klee/examples/linux-3.18.37/klee-last","symbol.def","/playpen/ziqiao/2project/klee/examples/linux-3.18.37");
    #parse.formatAll()
    parse.parseResult()
    #parse.parseAll()

        
