from optparse import OptionParser
import math
import re
import scipy
import os
import sys
import numpy
import scipy.sparse as sps
from scipy.sparse.csgraph import connected_components
import networkx as nx
class Data(object):
    def __init__(self, name):
        self.__name  = name
        self.__links = set()

    @property
    def name(self):
        return self.__name

    @property
    def links(self):
        return set(self.__links)

    def add_link(self, other):
        self.__links.add(other)
        other.__links.add(self)

# The function to look for connected components.
def connected_components(nodes):

    # List of connected components found. The order is random.
    result = []

    # Make a copy of the set, so we can modify it.
    nodes = set(nodes)

    # Iterate while we still have nodes to process.
    while nodes:

        # Get a random node and remove it from the global set.
        n = nodes.pop()

        # This set will contain the next group of nodes connected to each other.
        group = {n}

        # Build a queue with this node in it.
        queue = [n]

        # Iterate the queue.
        # When it's empty, we finished visiting a group of connected nodes.
        while queue:

            # Consume the next item from the queue.
            n = queue.pop(0)

            # Fetch the neighbors.
            neighbors = n.links

            # Remove the neighbors we already visited.
            neighbors.difference_update(group)

            # Remove the remaining nodes from the global set.
            nodes.difference_update(neighbors)

            # Add them to the group of connected nodes.
            group.update(neighbors)

            # Add them to the queue, so we visit them in the next iterations.
            queue.extend(neighbors)

        # Add the group to the list of groups.
        result.append(group)

    # Return the list of groups.
    return result

def isConcernedGroup(concerns,group):
	for node in concerns:
		if node in group:
			return True
	return False
def pause():
    a=raw_input('wait')

def loadCNF(filename):
    f=open(filename)
    concerned=set()
    nNode=0
    G=nx.Graph()
    for line in f:
        line=re.sub(' +',' ',line)
        if line.startswith('c ind') or line.startswith('c jac'):
            inds=line[6:].split(' ')
            inds=list(map(int,inds))
            concerned.update(inds[:len(inds)-1])
        elif line.startswith('c'):
            continue
        elif line.startswith('p'):
	    three=line.split(' ')
            nNode=int(three[2])
	elif line.endswith('0\n'):
            nodes=line.split(' ')
            nodes=nodes[:len(nodes)-1]
            nodes=list(map(abs,map(int,nodes)))
            #print nodes
            G.add_path(nodes);
    print "finish building graph"
    #com= connected_components(graph)
    #com=nx.connected_components(G)

    #print result
    #com=result[1]
    #print com
    validNodes=set([])
    number=0
    for node in concerned:
        #print node
        if node not in validNodes:
            com=nx.node_connected_component(G,node)
            print "finish components"
            validNodes.update(com)
        #concerned.difference_update(validNodes)
    f.close()
    f=open(filename)
    newf=open(filename+'.simp','w+')
    delete=False
    for line in f:
        if line.endswith('0\n') and not line.startswith('c'):
            delete=True
            nodes=line.split(' ')
            nodes=nodes[:len(nodes)-1]
            nodes=list(map(int,nodes))
            for node in nodes:
                node=abs(node)
                if node in validNodes:
                    delete=False;
        if delete:
            continue
        else:
            newf.write(line);
    f.close()
    newf.close()


def loadCNF_custom(filename):
    f=open(filename)
    concerned=[]
    nNode=0
    graph=set()
    nodeMap={}
    for line in f:
        line=re.sub(' +',' ',line)
        if line.startswith('c ind') or line.startswith('c jac'):
            inds=line[6:].split(' ')
            inds=list(map(int,inds))
            concerned=concerned+inds[:len(inds)-1]
        elif line.startswith('c'):
            continue
        elif line.startswith('p'):
	    three=line.split(' ')
            nNode=int(three[2])
	elif line.endswith('0\n'):
            nodes=line.split(' ')
            nodes=nodes[:len(nodes)-1]
            nodes=list(map(int,nodes))
            #print nodes
            l=len(nodes)
            if l==1:
                continue
	    node0=abs(nodes[0])
	    if node0 not in nodeMap:
                nodeMap[node0]=Data(node0)
            for node in nodes:
                node=abs(node)
                if node not in nodeMap:
                        nodeMap[node]=Data(node)
                nodeMap[node0].add_link(nodeMap[node])
    for key in nodeMap:
        graph.add(nodeMap[key])
    print "finish building graph"
    com= connected_components(graph)
    print "finish components"
    #print result
    #com=result[1]
    #print com
    validNode=[]
    number=0
    for components in com:
        group = sorted(node.name for node in components)
        #print "Group #%i: %s" % (number, group)
        number=number+1
        if isConcernedGroup(concerned,group):
                validNode=validNode+group
    f.close()
    f=open(filename)
    newf=open(filename+'.simp','w+')
    delete=False
    for line in f:
        if line.endswith('0\n') and not line.startswith('c'):
            delete=True
            nodes=line.split(' ')
            nodes=nodes[:len(nodes)-1]
            nodes=list(map(int,nodes))
            for node in nodes:
                node=abs(node)
                if node in validNode:
                    delete=False;
        if delete:
            continue
        else:
            newf.write(line);
    f.close()
    newf.close()




def loadCNF_old(filename):
    f=open(filename)
    concerned=[]
    for line in f:
        line=re.sub(' +',' ',line)
        if line.startswith('c ind') or line.startswith('c jac'):
            inds=line[6:].split(' ')
            inds=list(map(int,inds))
            concerned=concerned+inds[:len(inds)-1]
        elif line.startswith('c'):
            continue
        elif line.startswith('p'):
            three=line.split(' ')
            nNode=int(three[2])
            # data=numpy.zeros(shape=(nNode,nNode),dtype='int',)
            rows=nNode
            cols=nNode
            data= sps.coo_matrix((rows, cols))
            #print data
        elif line.endswith('0\n'):
            nodes=line.split(' ')
            nodes=nodes[:len(nodes)-1]
            nodes=list(map(int,nodes))
            #print nodes
            l=len(nodes)
            if l==1:
                continue
            for k in range(0,l-1):
                #print abs(nodes[k]),abs(nodes[k+1])
                data=data+sps.coo_matrix(([1],([abs(nodes[k])-1],[abs(nodes[k+1])-1])),shape=(rows,cols))
    group={}
    print "start to find connect components"

    result= connected_components(data,connection='weak')
    print result
    com=result[1]
    #print com
    for node in concerned:
        #print node
        group_concerned=com[node-1]
        if group_concerned not in group:
            group[group_concerned]=[node]
        else:
            group[group_concerned].append(node)
    validNode=[]
    for group_concerned in group:
        group_nodes=list(numpy.array(numpy.where(com==group_concerned)[0])+1)
        #print len(group_nodes)
        n_group_nodes=numpy.where(com!=group_concerned)
        print group[group_concerned],':',group_nodes,n_group_nodes
        validNode=validNode+group_nodes
    f.close()
    f=open(filename)
    newf=open(filename+'.simp','w+')
    delete=False
    for line in f:
        if line.endswith('0\n') and not line.startswith('c'):
            delete=True
            nodes=line.split(' ')
            nodes=nodes[:len(nodes)-1]
            nodes=list(map(int,nodes))
            for node in nodes:
                if node in validNode:
                    delete=False;
        if delete:
            continue
        else:
            newf.write(line);
    f.close()
    newf.close()

def simplifyCNF(cnffile):
	return loadCNF(cnffile)

queryForOb={}
def pushRelationIntoOutside(outsideX,outsideY,index):
    if len(outsideX)<=len(outsideY):
        outsideX.append(index)
    else:
        outsideY.append(index)
        outsideX.append(index)

def EndExpr(queryread):
    if queryread.count('(')==queryread.count(')') and queryread.count('[')==queryread.count(']'):
        return True
    else:
        return False

def loadPC(pcfile,concerned):
    f=open(pcfile)
    read=f.read()
    declareend=read.find('(')
    declare=read[:declareend]
    querystart=read.find('query [')+len('query [')
    queryend=read.rfind(']',0,read.rfind('false'))
    query=read[querystart:queryend]
    querys=query.split('\n')
    declare=declare.split('\n')
    assignIndex={}
    concernedIndex=[]
    index=0
    for line in declare:
        line=line.split(' ')
        if len(line)<2:
            continue
        symsize=line[1]
        symsize=symsize.replace(']','')
        symsize=symsize.split('[')
        sym=symsize[0]
        if sym in concerned:
            for offset in concerned[sym]:
                concernedIndex.append(offset+index)
        size=int(symsize[1])
        assignIndex[sym]=(index,size)
        index=index+size
    rows=index+1
    cols=index+1
    nLine=0
    querylst=[]
    while nLine<len(querys):
        line=querys[nLine]
        while not (line.count('(')==line.count(')') and line.count('[')==line.count(']')):
            nLine=nLine+1
            line=line+' '+querys[nLine]
        nLine=nLine+1

        querylst.append(line)


    queryIndexStart=rows
    rows=rows+len(querylst)
    cols=cols+len(querylst)

    data= sps.coo_matrix((rows, cols))
    queryIndex=queryIndexStart-1
    bindings={}
    for line in querylst:
        #print line
        queryIndex=queryIndex+1
        outsideX=[queryIndex]
        #outsideX=[queryIndex]
        outsideY=[]
        pos=0
        #print line
        bindingIndex=0
        while True:
            bindingIndex=line.find(':',bindingIndex+1);
            if bindingIndex>=0:
                bindinglabelIndex=line.rfind(' ',0,bindingIndex)+1
                bindinglabel=line[bindinglabelIndex:bindingIndex]
                if ( bindinglabel.startswith('U') or bindinglabel.startswith('N')):
                    bindingEnd=line.find(')',bindingIndex)+1
                    bindingExpr=line[bindingIndex:bindingEnd]
                    while not EndExpr(bindingExpr):
                        bindingEnd=line.find(')',bindingEnd)+1
                        #print bindingExpr
                        bindingExpr=line[bindingIndex:bindingEnd]
                    bindings[bindinglabel]=queryIndex;
            else:
                break;
        for label in bindings:
            if label in line:
                pushRelationIntoOutside(outsideX,outsideY,bindings[label])
        #print bindings
        while True:
            startread=line.find('(Read',pos)
            if startread<0:
                break
            endread=line.find(')',startread)
            queryread=line[startread:endread+1]
            while not (queryread.count('(')==queryread.count(')') and queryread.count('[')==queryread.count(']')):
                endread=line.find(')',endread+1)
                queryread=line[startread:endread+1]
            pos=startread+4
            #print 'query read=',queryread
            queryread=queryread[1:len(queryread)-1]
            queryread=re.sub(' +',' ',queryread)
            queryread=queryread.split(' ')
            numElement=0
            element=[]
            i=1
            while i<len(queryread):
                one=queryread[i]
                while not (one.count('(')==one.count(')') and one.count('[')==one.count(']')):
                    i=i+1
                    one=one+' '+queryread[i]
                    #print one,one.count('('),one.count(')')
                i=i+1
                element.append(one)
                numElement=numElement+1
            if not  numElement==3:
                #print 'error num elemet for read',element
                if numElement>=4 and element[3]=='@':
                    print element
                    element[2]=element[4]
                else:
                    print "error",element
                    os.system("cp "+pcfile+ ' '+pcfile+'.simp')

            #print element
            size=element[0]
            size=int(size[1:])/8 
            offset=element[1]
            sym=element[2]
            
            if not assignIndex.has_key(sym):
                #print 'skip',sym
                continue
            two=assignIndex[sym]
            index=two[0]
            symsize=two[1]
            if '(' in offset or 'U' in offset or 'N' in offset:
                offset=0
                size=symsize
            else:
                offset=int(offset)
            x=[]
            y=[]
            #print 'size,ofest=',size,offset
            for i in range(1,size):
                x.append(i-1+offset+index)
                y.append(i+offset+index)
            #print x,y
            #print sym,offset+index
            if len(outsideX)<=len(outsideY):
                outsideX.append(offset+index)
            else:
                outsideY.append(offset+index)
                outsideX.append(offset+index)
            data=data+sps.coo_matrix(([1]*(size-1),(x,y)),shape=(rows,cols))
        outsidelen=min(len(outsideX),len(outsideY))
        #print outsidelen,len(outsideX),len(outsideY)
        outsideX=outsideX[0:outsidelen]
        outsideY=outsideY[0:outsidelen]
        #print outsidelen,len(outsideX),len(outsideY),outsideX,outsideY
        data=data+sps.coo_matrix(([1]*outsidelen,(outsideX,outsideY)),shape=(rows,cols))
    result= connected_components(data,connection='weak')
    com=result[1]
    group_concerned={}
    #print data
    for ci in concernedIndex:
        group=com[ci]
        if group not in group_concerned:
            group_concerned[group]=[ci]
        else:
            group_concerned[group].append(ci)
    validquery=[]
    for group in group_concerned:
        
        nodeInGroup=numpy.where(com==group)
        #print group_concerned[group],":",nodeInGroup
        for node in nodeInGroup[0]:
            if node>=queryIndexStart:
                validquery.append( querylst[node-queryIndexStart])
    #print 'query=','\n'.join(validquery)
    if len(validquery)<2:
        #print validquery
        pause()
    else:
        if validquery[0] in queryForOb:
            q='\n'.join(validquery[1:])
            if q not in  queryForOb[validquery[0]]:
                queryForOb[validquery[0]].append(q)
        else:
            queryForOb[validquery[0]]=['\n'.join(validquery[1:])]
    write=read[0:querystart]+'\n'.join(validquery)+'\n'+read[queryend:]
    f=open(pcfile+'.simp','w+')
    f.write(write)
    f.close()
    return pcfile+'.simp'


def printOutput():
    for key in queryForOb:
        print key,queryForOb[key]
def simplifyPC(pcfile,concerned):
    return loadPC(pcfile,concerned)

def loadCNFOpt(option, opt, value, parser):
    argv=parser.rargs
    loadCNF(argv[0])

def loadCNFOpt2(option, opt, value, parser):
    argv=parser.rargs
    loadCNF_custom(argv[0])

parser=OptionParser()

parser.add_option('-c',"--simplify-cnf",action="callback",callback=loadCNFOpt2)
parser.add_option('-s',"--simplify",action="callback",callback=loadCNFOpt)
parser.parse_args()
#concerned={'tk':[1128,1129,1130,1131],'observable':[0]}
#loadPC(sys.argv[1],concerned)
#loadCNF(sys.argv[1])





