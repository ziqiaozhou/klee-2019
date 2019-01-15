file=$1
out=$2
cfile="concern.txt"
jfile="jaccard.txt"
#kleaver -out=$out.smt2 --print-smtlib $file
#stp --output-CNF --disable-simplifications -r $out.smt2
cp output_0.cnf ${out}.cnf
python /playpen/ziqiao/2project/klee/analyzer/SetInd.py ${out}.cnf name_cnf.txt $cfile $jfile
