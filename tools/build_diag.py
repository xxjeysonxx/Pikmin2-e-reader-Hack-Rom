"""Construye Pikmin72_Diag0.gba: ROM de DIAGNOSTICO.

Identica a Pikmin72_RealSave.gba salvo dos cosas:
  1. Hook de diagnostico en 0x740D00 que fuerza el cursor de ficha a 0
     (el stub le suma 1 -> siempre la FICHA 1, sin leer teclas).
  2. El literal de 0x90B0 apunta a ese hook.

Si con esta ROM el juego siempre ensena el mismo nivel, el hook se ejecuta.
Si sigue avanzando como siempre, el hook no se ejecuta.
"""
import hashlib
import struct

SRC = "Pikmin72_RealSave.gba"
DST = "Pikmin72_Diag0.gba"
HOOK_FILE = "keyhook_diag.bin"
HOOK_OFF = 0x740D00
HOOK_ADDR = 0x08000000 + HOOK_OFF
LIT_OFF = 0x90B0

rom = bytearray(open(SRC, "rb").read())
hook = open(HOOK_FILE, "rb").read()
assert len(rom) == 0x800000, "ROM no es de 8 MiB"
assert len(hook) < 0x300, "hook demasiado grande"

assert all(b == 0xFF for b in rom[HOOK_OFF:HOOK_OFF + 0x100]), "la zona del hook no esta libre"
rom[HOOK_OFF:HOOK_OFF + len(hook)] = hook

old = struct.unpack_from("<I", rom, LIT_OFF)[0]
assert old == 0x08740CA1, "literal inesperado: 0x%08X" % old
struct.pack_into("<I", rom, LIT_OFF, HOOK_ADDR | 1)

open(DST, "wb").write(rom)
print("escrito", DST, len(rom), "bytes")
print("sha256:", hashlib.sha256(rom).hexdigest())
print("hook   : 0x%08X (%d B)  -> cursor = 0 siempre" % (HOOK_ADDR, len(hook)))
print("literal: 0x%08X -> 0x%08X" % (old, HOOK_ADDR | 1))
