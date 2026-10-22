"""Prueba unitaria del hook de seleccion con Unicorn (ARM Thumb).

El hook ahora BLOQUEA hasta que se pulse: primero espera a que no haya nada
pulsado (para no dispararse con una tecla que venias manteniendo) y despues
espera la pulsacion. Por eso el test inyecta una SECUENCIA de estados de
KEYINPUT a lo largo de la ejecucion, no un estado fijo.

Tambien mide el efecto NETO (hook + el +1 incondicional del stub), que es lo
que ve el usuario. Medir el hook aislado escondia un bug de la cuenta.
"""
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_MODE_THUMB, UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_SP, UC_ARM_REG_LR

HOOK_ADDR = 0x08740D00
WRAPPER = 0x08740CA1
KEYINPUT = 0x04000130
CURSOR = 0x0202F8A0
N = 72

hook = open("keyhook.bin", "rb").read()

BIT_A, BIT_B, BIT_SELECT, BIT_START = 0, 1, 2, 3
BIT_RIGHT, BIT_LEFT, BIT_UP, BIT_DOWN = 4, 5, 6, 7
BIT_R, BIT_L = 8, 9


def keys(*bits):
    """KEYINPUT es activo-bajo: bit a 0 = tecla pulsada."""
    v = 0x03FF
    for b in bits:
        v &= ~(1 << b)
    return v


def run_hook(eventos, cursor_in, max_instr=20000):
    """eventos: [(n_instruccion, valor_KEYINPUT), ...]

    Devuelve (cursor, instrucciones, llego_al_wrapper).
    """
    mu = Uc(UC_ARCH_ARM, UC_MODE_ARM | UC_MODE_THUMB)
    mu.mem_map(0x08000000, 0x800000)
    mu.mem_map(0x02000000, 0x40000)
    mu.mem_map(0x04000000, 0x1000)
    mu.mem_write(HOOK_ADDR, hook)
    mu.mem_write(CURSOR, cursor_in.to_bytes(4, "little"))
    mu.reg_write(UC_ARM_REG_SP, 0x0203F000)
    mu.reg_write(UC_ARM_REG_LR, 0x08000000)

    pend = list(eventos)
    # estado inicial: el del primer evento
    mu.mem_write(KEYINPUT, pend[0][1].to_bytes(2, "little"))
    st = {"done": False, "n": 0}

    def on_code(uc, address, size, user):
        if address == (WRAPPER & ~1):
            st["done"] = True
            uc.emu_stop()
            return
        st["n"] += 1
        while len(pend) > 1 and st["n"] >= pend[1][0]:
            pend.pop(0)
            uc.mem_write(KEYINPUT, pend[0][1].to_bytes(2, "little"))

    mu.hook_add(UC_HOOK_CODE, on_code)
    mu.emu_start(HOOK_ADDR | 1, 0, count=max_instr)
    c = int.from_bytes(mu.mem_read(CURSOR, 4), "little")
    return c, st["n"], st["done"]


def neto(eventos, cursor_in):
    c, n, done = run_hook(eventos, cursor_in)
    if not done:
        return None, n
    d = c - cursor_in
    if d > N // 2:
        d -= N
    elif d < -(N // 2):
        d += N
    return d + 1, n


def sec(*kv):
    """Secuencia: nada -> nada, y a las 20 instrucciones el estado dado."""
    return [(0, keys()), (20, keys(*kv))]


casos = [
    # nombre,                        eventos,                          cursor, neto
    ("pulsa R",                      sec(BIT_R),                       5,  +1),
    ("pulsa Derecha",                sec(BIT_RIGHT),                   5,  +1),
    ("pulsa L",                      sec(BIT_L),                       5,  -1),
    ("pulsa Izquierda",              sec(BIT_LEFT),                    5,  -1),
    ("pulsa A",                      sec(BIT_A),                       5,  +1),
    ("pulsa Start",                  sec(BIT_START),                   5,  +1),
    ("pulsa B+R",                    sec(BIT_B, BIT_R),                5, +10),
    ("pulsa B+L",                    sec(BIT_B, BIT_L),                5, -10),
    ("L en cursor 0 (envolver)",     sec(BIT_L),                       0,  -1),
    ("R en cursor 71 (envolver)",    sec(BIT_R),                      71,  +1),
    ("B+L en cursor 3 (envolver)",   sec(BIT_B, BIT_L),                3, -10),
    # venia con R pillada: suelta y luego pulsa L -> debe dar -1, no +1
    ("R pillada, suelta, pulsa L",   [(0, keys(BIT_R)), (40, keys()), (120, keys(BIT_L))], 5, -1),
]

ok = 0
for nombre, ev, cin, esperado in casos:
    d, n = neto(ev, cin)
    good = d == esperado
    ok += good
    print("%-30s c=%-2d  neto %+3s  esperado %+3d  %5d instr.  %s"
          % (nombre, cin, "?" if d is None else "%+d" % d, esperado, n,
             "OK" if good else "FALLO"))

print()
print("%d/%d casos OK" % (ok, len(casos)))

# --- NO debe escanear solo ---
bloqueos = [
    ("no pulsas nada",              [(0, keys())]),
    ("solo B (es modificador)",     [(0, keys()), (20, keys(BIT_B))]),
    ("solo arriba",                 [(0, keys()), (20, keys(BIT_UP))]),
    ("R pillada y no sueltas",      [(0, keys(BIT_R))]),
]
print()
for nombre, ev in bloqueos:
    _, n, done = run_hook(ev, 5, max_instr=4000)
    good = not done
    ok += good
    print("%-30s bloquea=%s tras %5d instr.  %s"
          % (nombre, "si" if not done else "NO", n, "OK" if good else "FALLO"))

# --- el cursor nunca sale de 0..71 ---
malos = [c for c in range(N)
         for kv in ((BIT_L,), (BIT_R,), (BIT_B, BIT_L), (BIT_B, BIT_R))
         if not (0 <= run_hook(sec(*kv), c)[0] < N)]
print()
print("fuera de rango 0..71:", "ninguno" if not malos else malos)
