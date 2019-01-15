import sys
import math
import os
from pyparsing import nestedExpr
def is_int(s):
    try: 
        int(str(s))
        return True
    except ValueError:
        return False

def loadDef(def_name):
    def_file=open(def_name);
    def_type={}
    for line in def_file:
        lst = line.split(":")
        def_type[lst[0]]=lst[1]
    def_file.close()
    return def_type

def loadStruct(struct,linuxfolder):
    structname=struct.strip("struct").strip(" ").strip("\n");
    f=open(structname+".struct");
    elements={}
    for line in f:
        line=line.split();
        if not elements.has_key(line[0]):
            elements[line[0]]=[]
        elements[line[0]].append((line[1],line[2]));
    f.close()
    return elements

starters=['Eq','Ne','Ult','Ule','Ugt','Uge','Slt','Sle','Sgt','Sge']
def isBranch(one):
    for key in starters:
        if one.startswith("['"+key+"'"):
            return True
    return False
logic={'And':[2,3], 'Or':[2,3], 'Xor':[2,3], 'Shl':[2], 'LShr':[2], 'AShr':[2]}
def isLogic(one):
    for key in logic.keys():
        if str(one).startswith("['"+key+"'"):
            return key
    return ""

readKey=['ReadLSB','Read','ReadMSB']
def isRead(one):
    for key in readKeys():
        if str(one).startswith("['"+key+"'"):
            return True
    reutrn False

def convertOffset2Field(one):
    readwidth=one[1]
    readoffset=one[2]
    readobj=one[3]
    symbol_type
def convertDec2Hex(one):
    key=isLogic(one)
    if not key=="":
        for pos in logic[key]:
            if len(one)>pos:
                if is_int(one[pos]):
                    one[pos]=str(hex(int(one[pos])))
    return one
def  printNested(of,nest):
    noprint=True
    for one in nest:
        findOne=False
        one=convertDec2Hex(one);
        for oneone in one:
            if isinstance(oneone,list):
                if not findOne:
                    findOne=True
                    one=printNested(of,one)
    one=convertDec2Hex(one)
    if isBranch(str(nest)):
        of.write(str(nest)+'\n')
    return one

def parsePC(path_str):
    start=path_str.find('(query')
    path_str=path_str[start:];
    path_str=path_str.replace("\n","")
    result=nestedExpr(opener='(',closer=')').parseString(path_str).asList()
    return result


structs={}
readKeys=['ReadLSB','Read','ReadMSB']
typewidths=[32,16,8]
def parsePath(pathfile,symbolfile,linuxfolder):
    pathf=open(pathfile);
    pathc=pathf.read();
    whole=pathc;
    symbol_type=loadDef(symbolfile);
    for symbol in symbol_type.keys():
        stype=symbol_type[symbol]
        if not structs.has_key(stype):
            structs[stype]=loadStruct(stype,linuxfolder);
        structdic=structs[stype]
        offsets=structdic.keys()

        for cindex in range(0,len(offsets)):
            coffset=offsets[cindex]
            for key in readKeys:
                for width in typewidths:
                    sindex=0;
                    allname=[]
                    while offsets[sindex+cindex]-coffset<width:
                        offset=offsets[sindex]
                        index=sindex+cindex;
                        sindex=sindex+1
                        name_type=structdic[coffset];
                        names=[];
                        for candidate in name_type:
                            names.append(candidate[0]);
                        allname.append(names);
                        if index<len(offsets)-1:
                            for roffset in range(int(offset),int(offsets[index+1]),8):
                                whole=whole.replace(key+' '+w+' '+str(int(roffset)/8)+' '+symbol,symbol+'->'+'/'.join(names))
                    else:
                        whole=whole.replace(key+' '+w+' '+str(int(offset)/8)+' '+symbol,symbol+'->'+'/'.join(names))
    outfile=pathfile.replace('.pc','.pc.new')
    exprfile=pathfile.replace('.pc','.pc.expr')
    print outfile,exprfile
    of=open(outfile,'w+')
    exprof=open(exprfile,'w+')
    of.write(whole)
    exprs=parsePC(whole)
    print exprs
    exprs=printNested(exprof,exprs)
    of.close();
    exprof.close()

def parseAll(pathDir,symbolfile,linuxfolder):
    for pathfile in os.listdir(pathDir):
        if pathfile.endswith(".pc"):
            parsePath(pathDir+'/'+pathfile,symbolfile,linuxfolder);
        

if len(sys.argv)>3:
    parseAll(sys.argv[1],sys.argv[2],sys.argv[3])

        
