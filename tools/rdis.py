import capstone,struct,sys
rom=open('Pikmin72_RealSave.gba','rb').read()
md=capstone.Cs(capstone.CS_ARCH_ARM,capstone.CS_MODE_THUMB)
def rd32(a): return struct.unpack_from('<I',rom,a-0x08000000)[0]
def listing(start,end):
    out=[]
    for i in md.disasm(rom[start-0x08000000:end-0x08000000],start):
        note=''
        ops=i.op_str
        if i.mnemonic=='ldr' and '[pc,' in ops:
            try:
                imm=int(ops.split('#')[1].rstrip(']'),0)
                lit=(i.address+4)&~3
                lit+=imm
                v=rd32(lit)
                note='   ; [%08X]=%08X'%(lit,v)
            except Exception: pass
        out.append('%08X  %-10s %-26s%s'%(i.address,i.bytes.hex(),i.mnemonic+' '+ops,note))
    return '\n'.join(out)
if __name__=='__main__':
    a=int(sys.argv[1],16); b=int(sys.argv[2],16)
    print(listing(a,b))
