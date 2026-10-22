"""Descomprime el chunk gbAs de un savestate de mGBA a RAM cruda.

Uso: python _ss.py <entrada.ss1> <salida.bin>
"""
import struct
import sys
import zlib


def extraer_gbas(path):
    d = open(path, "rb").read()
    if d[:8] != b"\x89PNG\r\n\x1a\n":
        return d  # ya es crudo
    off = 8
    while off + 8 <= len(d):
        ln = struct.unpack_from(">I", d, off)[0]
        typ = d[off + 4:off + 8]
        cuerpo = d[off + 8:off + 8 + ln]
        if typ == b"gbAs":
            return zlib.decompress(cuerpo)
        off += 12 + ln
    raise SystemExit("no hay chunk gbAs")


if __name__ == "__main__":
    src = sys.argv[1]
    dst = sys.argv[2]
    raw = extraer_gbas(src)
    open(dst, "wb").write(raw)
    print("%s -> %s  %d bytes" % (src, dst, len(raw)))
