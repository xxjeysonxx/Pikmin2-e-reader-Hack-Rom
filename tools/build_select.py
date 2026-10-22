"""Construye Pikmin72_Select.gba a partir de Pikmin72_RealSave.gba.

Cambios:
  1. Hook propio en 0x740D00 (72 B): lee KEYINPUT y mueve el cursor de ficha.
  2. El literal del hook en 0x90B0 pasa a apuntar a 0x08740D01.
  3. Tope del cursor en el stub: 0x2B (43) -> 0x48 (72), para que las 72
     fichas sean alcanzables.

Nada mas se toca. El stub original, el save y las 72 fichas quedan igual.
"""
import hashlib
import shutil
import struct

SRC = "Pikmin72_RealSave.gba"
DST = "Pikmin72_Select.gba"
HOOK_FILE = "keyhook.bin"
HOOK_OFF = 0x740D00
HOOK_ADDR = 0x08000000 + HOOK_OFF
LIT_OFF = 0x90B0
CLAMP_OFF = 0x740C0C
CLAMP_OLD = 0x2B
CLAMP_NEW = 0x48

rom = bytearray(open(SRC, "rb").read())
hook = open(HOOK_FILE, "rb").read()
assert len(rom) == 0x800000, "ROM no es de 8 MiB"
assert len(hook) < 0x300, "hook demasiado grande"

# 1) zona libre
assert all(b == 0xFF for b in rom[HOOK_OFF:HOOK_OFF + 0x100]), "la zona del hook no esta libre"
rom[HOOK_OFF:HOOK_OFF + len(hook)] = hook

# 2) literal del hook
old = struct.unpack_from("<I", rom, LIT_OFF)[0]
assert old == 0x08740CA1, "literal inesperado: 0x%08X" % old
struct.pack_into("<I", rom, LIT_OFF, HOOK_ADDR | 1)

# 3) tope del cursor: el toolkit ya escribe cards.length en 0x740C0C, que es
#    justo el inmediato de "movs r2,#imm8" (el tope de envoltura). Con 72 fichas
#    vale 0x48. Solo se comprueba.
assert rom[CLAMP_OFF] == CLAMP_NEW, "tope inesperado: 0x%02X" % rom[CLAMP_OFF]
assert rom[CLAMP_OFF + 1] == 0x22, "no parece movs r2,#imm8"

open(DST, "wb").write(rom)
h = hashlib.sha256(rom).hexdigest()
print("escrito", DST, len(rom), "bytes")
print("sha256:", h)
print("hook   : 0x%08X (%d B)" % (HOOK_ADDR, len(hook)))
print("literal: 0x%08X -> 0x%08X" % (old, HOOK_ADDR | 1))
print("tope   : 0x%02X -> 0x%02X" % (CLAMP_OLD, CLAMP_NEW))
