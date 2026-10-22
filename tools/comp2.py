import struct
from PIL import Image
d=open('ram_dump.bin','rb').read()
pal=d[0x800:0xC00]
v=open('vram_ss.bin','rb').read()
def rgb(i):
    c=struct.unpack_from('<H',pal,i*2)[0]
    r=(c&0x1F)<<3; g=((c>>5)&0x1F)<<3; b=((c>>10)&0x1F)<<3
    return (r|r>>5,g|g>>5,b|b>>5)
BG=[(0,0xC000),(0,0xD000),(0,0xE000),(0x4000,0xF000)]
W,H=240,160
for bg,(char,screen) in enumerate(BG):
    img=Image.new('RGB',(W,H),(20,20,20)); px=img.load()
    for y in range(H):
        ty=y//8
        for x in range(W):
            tx=x//8
            e=struct.unpack_from('<H',v,screen+(ty*64+tx)*2)[0]
            tile=(e&0x3FF); pb=((e>>12)&0xF)
            b=v[char+tile*32+(y%8)*4+(x%8)//2]
            idx=(b>>4) if (x%8)%2==0 else (b&0xF)
            if idx: px[x,y]=rgb(pb*16+idx)
    img.resize((W*3,H*3),Image.NEAREST).save('bg%d.png'%bg)
print('ok')
