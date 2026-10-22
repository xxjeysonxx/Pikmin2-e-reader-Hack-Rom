"""Decodificador VPK0 (Nintendo) - puerto fiel de tehzz/vpk0.

Formato:
  header 9 B: "vpk0" + u32 BE (tamano descomprimido) + u8 metodo (0=one sample, 1=two sample)
  arbol Huffman de offsets
  arbol Huffman de longitudes
  datos

Arbol: se lee bit a bit.
  bit 0 -> hoja: se leen 8 bits (el "bitsize" del valor)
  bit 1 -> nodo: si hay <2 pendientes, fin; si no, combina los dos ultimos
Raiz = ultima entrada. Recorrido: bit 1 -> derecha, bit 0 -> izquierda.
La hoja da el NUMERO DE BITS a leer para el valor real.

Datos: bit 1 -> copyback, bit 0 -> literal de 8 bits.
"""


class BitReader:
    __slots__ = ("data", "pos", "n")

    def __init__(self, data, start_byte=0):
        self.data = data
        self.pos = start_byte * 8
        self.n = len(data) * 8

    def bit(self):
        if self.pos >= self.n:
            raise EOFError("fin de stream vpk0")
        byte = self.data[self.pos >> 3]
        b = (byte >> (7 - (self.pos & 7))) & 1
        self.pos += 1
        return b

    def bits(self, count):
        v = 0
        for _ in range(count):
            v = (v << 1) | self.bit()
        return v

    @property
    def byte_pos(self):
        return (self.pos + 7) >> 3


LEAF = 0
NODE = 1


def read_tree(br):
    """Devuelve la lista de entradas; la raiz es la ultima."""
    entries = []  # (tipo, valor) ; NODE guarda (izq, der)
    pending = []
    while True:
        new_idx = len(entries)
        if br.bit():
            if len(pending) < 2:
                break
            right = pending.pop()
            left = pending.pop()
            entries.append((NODE, left, right))
        else:
            entries.append((LEAF, br.bits(8)))
        pending.append(new_idx)
    return entries


def tree_value(tree, br):
    if not tree:
        return 0
    idx = len(tree) - 1
    while tree[idx][0] == NODE:
        _, left, right = tree[idx]
        idx = right if br.bit() else left
    return br.bits(tree[idx][1])


def decode(data, start_byte=0):
    """Descomprime un stream vpk0. Devuelve (salida, info)."""
    if data[start_byte:start_byte + 4] != b"vpk0":
        raise ValueError("no es un stream vpk0")
    size = int.from_bytes(data[start_byte + 4:start_byte + 8], "big")
    method = data[start_byte + 8]
    if method not in (0, 1):
        raise ValueError("metodo vpk0 invalido: %d" % method)

    br = BitReader(data, start_byte + 9)
    offsets = read_tree(br)
    lengths = read_tree(br)

    out = bytearray()
    while len(out) < size:
        if br.bit():
            initial = tree_value(offsets, br)
            if method == 1:
                if initial < 3:
                    low = initial + 1
                    upper = tree_value(offsets, br)
                    move_back = (low + (upper << 2)) - 8
                else:
                    move_back = (initial << 2) - 8
            else:
                move_back = initial
            if move_back > len(out) or move_back <= 0:
                raise ValueError("lookback invalido %d en 0x%X" % (move_back, len(out)))
            length = tree_value(lengths, br)
            start = len(out) - move_back
            for i in range(start, start + length):
                out.append(out[i])
        else:
            out.append(br.bits(8))

    return bytes(out[:size]), {
        "size": size,
        "method": method,
        "bytes_consumidos": br.byte_pos - start_byte,
        "bits_consumidos": br.pos - start_byte * 8,
    }


def find_stream(data, magic=b"vpk0", start=0):
    i = data.find(magic, start)
    return -1 if i < 0 else i


if __name__ == "__main__":
    import sys
    d = open(sys.argv[1], "rb").read()
    i = find_stream(d)
    if i < 0:
        raise SystemExit("sin vpk0")
    out, info = decode(d, i)
    print("offset=0x%X  desc=%d  metodo=%d  consumidos=%d" % (i, len(out), info["method"], info["bytes_consumidos"]))
    open(sys.argv[2], "wb").write(out)
