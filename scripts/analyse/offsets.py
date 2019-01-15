import sys
import gdb
sys.setrecursionlimit(10000) 
class offsets(gdb.Command):
    def __init__(self):
        super (offsets, self).__init__ ('offsets-of', gdb.COMMAND_DATA)
    def printOneField(self,field,f,prev,base):
        ftype=gdb.types.get_basic_type(field.type)
        code=field.type.strip_typedefs().code
        offset=base+field.bitpos
        if code==gdb.TYPE_CODE_STRUCT:
            if field.name:
                prev=prev+field.name+"."
                self.printFields(f,ftype,prev,base+field.bitpos)
        elif code==gdb.TYPE_CODE_UNION:
            if field.name:
                prev=prev+field.name+"."
            self.printFields(f,ftype,prev,base+field.bitpos)
        elif code==gdb.TYPE_CODE_ARRAY:
            arrayT=ftype.target()
            arrayT=arrayT.strip_typedefs()
            count=ftype.sizeof/arrayT.sizeof
            name=field.name
            for i in range(0,count):
                one=field
                one.type=arrayT.strip_typedefs();
                one.name=name+"["+str(i)+"]"
                one.is_base_class=(arrayT.strip_typedefs().code>gdb.TYPE_CODE_ENUM);
                offset=offset+(i)*arrayT.sizeof*8
                self.printOneField(one,f,prev,offset)
        elif field.is_base_class==True:
            #print '    %s\t%d\t%s' % (field.name, base+field.bitpos,ftype.name)
            if ftype.name:
                tobewrite=str(field.bitpos+base)+"\t"+prev+field.name+"\t"+ftype.name+"\n"
            else:
                tobewrite=str(field.bitpos+base)+"\t"+prev+field.name+"\t"+"u"+str(ftype.sizeof)+"\n";
            f.write(tobewrite);
        else:
            if ftype.name:
                tobewrite=str(field.bitpos+base)+"\t"+prev+field.name+"\t"+ftype.name+"\n";
            else:
                tobewrite=str(field.bitpos+base)+"\t"+prev+field.name+"\tu"+str(ftype.sizeof)+"\n"
            f.write(tobewrite);

    def printFields(self,f,stype,prev,base):
        stype=stype.strip_typedefs();
        for field in stype.fields():
            offset=base+field.bitpos
            #print '    %s\t%d\t%s\t%d' % (field.name,base+ field.bitpos//8, field.type.tag,field.type.code)
            self.printOneField(field,f,prev,base);
        return 0
    def invoke(self, arg, from_tty):
        argv = gdb.string_to_argv(arg)
        if len(argv) != 1:
            raise gdb.GdbError('offsets-of takes exactly 1 argument.')
        stype = gdb.lookup_type(argv[0])
        str0=argv[0]
        words=str0.split();
        f = open(words[1]+".struct",'w')
        #print argv[0], '{'
        self.printFields(f,stype,"",0)
        #print '}'
        f.close()
    
