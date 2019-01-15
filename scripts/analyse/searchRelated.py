from pyparsing import nestedExpr

readKeys=['ReadLSB','Read','ReadMSB']
widths=[8,16,32,64]	
def nestSearch(keywords,expr,result):
	for one in expr:
		if type(one) is str:
			if one.startswith(keyword):
				result.append(expr)
		else if type(one) is list:
			nestSearch(keyword,one,result)


def searchElements(sym,pcfile):
    f=open(pcfile)
    read=f.read().replace('\n')
    read=read[read.find('query'):]
    exprs=nestedExpr(opener='(',closer=')').parseString(read).asList()
    allread=[]
    nestSearch([)

