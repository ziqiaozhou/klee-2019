import argparse
import os
import subprocess
def mergeAST(dirs,kleaver):
    pcfiles={}
    for d in dirs:
        if not os.path.isdir(d):
            continue
        blacklist=[]
        pcfiles[d]=[]
        for fname in os.listdir(d):
            if fname.endswith('.err'):
                name=fname.split('.')[0]
                blacklist.append(name)
            if fname.endswith('.pc'):
                name=fname.split('.')[0]
                pcfiles[d].append(name)
        for name in blacklist:
            pcfiles[d].remove(name)
    flist=[]
    print(pcfiles)
    for d in pcfiles:
        for name in pcfiles[d]:
            flist.append(os.path.join(d,name+'.pc'))
    cmd=kleaver+' -merge -outFormat=kquery --pc-all-const-widths=true '+' '.join(flist)
    print(cmd)
    result = subprocess.check_output(cmd, shell=True)
    #print result
    f=open('result.pc','w')
    index=result.find('#merge finished')
    f.write(result[index:])
    cmd='sed -i -e "s/v[0-9]*_\([a-zA-Z]*\)_[0-9]*/\1\g"'
    f.close()
def AST2CVC(fnames,kleaver):
    for fname in fnames:
        f=open(fname,'r')
        c=f.read()
        if True:
            f.close()
            f=open(fname,'w')
            f.write(c.replace('false)','false [] [offset])'))
        f.close()
        cmd=kleaver+' -printCVC --pc-all-const-widths=true '+fname
        print (cmd)
        os.system(cmd)
def STP2CNF(fnames,stp):
    for fname in fnames:
        cmd=stp+' --output-CNF --disable-simplifications -r '+fname
        print (cmd)
        os.system(cmd)
def AST2CNF(fnames,kleaver):
    for fname in fnames:
        f=open(fname,'r')
        c=f.read()
        f.close()
        f=open(fname,'w')
        f.write(c.replace('false)','false [] [secret])'))
        f.close()
        cmd=kleaver+' -evaluate --pc-all-const-widths=true '+fname
        print (cmd)
        os.system(cmd)

if __name__=="__main__":
    parser=argparse.ArgumentParser(description="convert kquery to CNF")
    parser.add_argument('inputs',type=str,nargs='+',help="input filenames")
    parser.add_argument('--kleaver',type=str,help="kleaver path",default='/playpen/ziqiao/thesis/codes/klee-all/klee/klee_build_dir/bin/kleaver')

    parser.add_argument('--stp',type=str,help="stp path",default='stp')
    parser.add_argument('--mode',type=str,help="mode: merge, tocnf",default='merge')
    args = parser.parse_args()
    mode=args.mode
    if 'merge' in mode:
       mergeAST(args.inputs,args.kleaver) 
    if 'ast2cnf' in mode:
        AST2CNF(args.inputs,args.kleaver)
    if 'cvc' in mode:
        AST2CVC(args.inputs,args.kleaver)
    if 'stp2cnf' in mode:
        STP2CNF(args.inputs,args.stp)
