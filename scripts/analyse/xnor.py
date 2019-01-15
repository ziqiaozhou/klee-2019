from z3 import *
from optparse import OptionParser
import numpy
import os
import re
import z3util
def _start_shell(local_ns=None):
          # An interactive shell is useful for debugging/development.
    import IPython
    user_ns = {}
    if local_ns:
        user_ns.update(local_ns)
        user_ns.update(globals())
        IPython.start_ipython(argv=[], user_ns=user_ns)

def simplify(filename,outfile="simplified.smt2"):
    solver=Solver();
    exprs=[]
    exp=z3.parse_smt2_file(filename)
    solver.add(exp)
    f=open(outfile,"w+")
    #print solver.sexpr()
    f.write(solver.to_smt2())
    f.close()


def XorFile(filenames,outfile="xnor.smt2"):
    solver=Solver();
    exprs=[]
    for filename in filenames:
        if filename.endswith(".smt2"):
            exp=z3.parse_smt2_file(filename)
            exprs.append(exp)

    #print Or(exprs)

    """for var in z3util.get_vars(exprs[0]):
        if var.sexpr() in name:
            svars.append(var);
    for svar in svars:
        z3.substitute(svar,mk_vars(svars.sexpr()+"2"))

    solver.add(noEqual)"""
    '''svar1=exprs[0]
    svar2=exprs[1]
    for var in z3util.get_vars(exprs[0]):
        if var.sexpr() == "secret":
            svar1=var;
    for var in z3util.get_vars(exprs[1]):
        if var.sexpr() == "secret2":
            svar2=var;
    '''
    print "read end"
    solver.add((And(exprs)))
    #solver.add(ForAll([svar1,svar2],Xor(exprs[0],exprs[1])))
    #e=Not(eq(svar1,svar2))
    #solver.add(e)
    f=open(outfile,"w+")
    #print solver.sexpr()
    f.write(solver.to_smt2())
    f.close()
    #_start_shell(locals())

def XorOpt(option, opt, value, parser):
    argv=parser.rargs;
    print option
    print opt
    if parser.values.filename and parser.values.mode=='xor':
        XorFile(argv,parser.values.filename);
    else:
        simplify(parser.values.infile,parser.values.filename);


parser = OptionParser()
parser.add_option("-o","--outfile",action="store", type="string",dest="filename")

parser.add_option("-i","--infile",action="store", type="string",dest="infile")
parser.add_option("-m","--mode",action="store", type="string",dest="mode")
parser.add_option("-x", "--xnor", action="callback",callback=XorOpt)

(options, args) = parser.parse_args()


