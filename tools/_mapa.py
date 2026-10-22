"""Renderiza el mapa completo de BG1 (64x32 tiles = 512x256) desde un savestate.

Muestra las dos mitades: izquierda (tx 0..31) hojas, derecha (tx 32..63) flores.
Uso: python _mapa.py <ram.bin> <salida.png>
"""
import struct
import sys

from PIL import Image

src = sys.argv[1] if len(sys.argv) > 1 else "ram_dump.bin"
dst = sys.argv[2] if len(sys.argv) > 2 else "mapa_completo.png"

d = open(src, "rb").read()
pal = d[0x800:0xC00]          # palette RAM 0x05000000
vram = d[0x1000:0x1000 + 0x18000]

CHAR = 0x0000                 # BG1 charbase 0x06000000
SCREEN = 0xD000               # BG1 mapbase 0x0600D000


def rgb(i):
    c = struct.unpack_from("<H", pal, i * 2)[0]
    r = (c & 0x1F) << 3
    g = ((c >> 5) & 0x1F) << 3
    b = ((c >> 10) & 0x1F) << 3
    return (r | r >> 5, g | g >> 5, b | b >> 5)


W, H = 512, 256
img = Image.new("RGB", (W, H), (18, 18, 26))
px = img.load()
for y in range(H):
    ty = y // 8
    for x in range(W):
        tx = x // 8
        e = struct.unpack_from("<H", vram, SCREEN + (ty * 64 + tx) * 2)[0]
        tile = e & 0x3FF
        pb = (e >> 12) & 0xF
        b = vram[CHAR + tile * 32 + (y % 8) * 4 + (x % 8) // 2]
        idx = (b >> 4) if (x % 8) % 2 == 0 else (b & 0xF)
        if idx:
            px[x, y] = rgb(pb * 16 + idx)

# separador vertical en tx=32 (la frontera entre las dos copias)
for y in range(H):
    px[255, y] = (255, 0, 128)
    px[256, y] = (255, 0, 128)

img.resize((W * 2, H * 2), Image.NEAREST).save(dst)
print("guardado", dst, "512x256 ->", img.size)
