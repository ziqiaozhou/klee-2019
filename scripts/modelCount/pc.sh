for f in `ls *.pc` ; 
do 
	sed -i '1s/(w8 \([0-9a-z]*\))/\1/g' $f
	sed -i 's/v[0-9]*_\([a-zA-Z0-9_]*\)_[0-9]*/\1/g' $f
done
