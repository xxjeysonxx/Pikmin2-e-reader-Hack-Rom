# pikmin2-eplus-toolkit

Herramientas de ingeniería inversa (RE) y parches para el **menú de fichas
Pikmin 2 (e-Reader+, Japón, PSAJ/ERDJ)** en Game Boy Advance.

Este repositorio contiene **solo código fuente propio y herramientas**: el
desensamblador, el decodificador VPK0, el hook de selección de ficha, los
scripts de composición de fondos y las recetas de GDB. **No incluye ningún
ROM comercial ni ninguna ficha (card) con derechos de autor.** Tú debes
aportar el ROM base y las fichas desde tu propia copia legal.

---

## ⚠️ Aviso legal (léelo)

- **No se distribuye** `Card e-Reader+ (Japan).gba`, `Pikmin72_RealSave.gba`,
  `Pikmin72_Select.gba`, `Pikmin72_Diag0.gba`, ni ningún `.sav`/`.ss1`/`.ss2`.
- **No se distribuyen** fichas (`.raw`) ni el directorio `eReaderWebToolkit/`
  (que depende del ROM comercial).
- Los scripts `build_real.js` / `parse_save.js` (que ensamblan el ROM de 8 MiB
  a partir del base comercial + save) **no están en este repo** por la misma
  razón.
- Lo que sí es original y redistribuible: `keyhook.s`/`keyhook.bin`,
  `keyhook_diag.bin`, `vpk0.py`, `rdis.py`, `comp*.py`, `test_keyhook.py` y
  demás utilidades listadas abajo.

Si clonas esto, necesitas tu propia copia legal del ROM base y regenerar
`Pikmin72_RealSave.gba` por tu cuenta para que `build_select.py` /
`build_diag.py` funcionen.

---

## Qué hay dentro

```
github/
├── README.md
├── .gitignore
├── LICENSE
└── tools/
    ├── keyhook.s          # código fuente (ASM Thumb) del hook de selección L/R
    ├── keyhook.bin        # hook compilado (72 B) — código propio
    ├── keyhook_diag.bin   # variante de diagnóstico (cursor=0) — código propio
    ├── build_select.py    # parchea RealSave.gba -> Select.gba (inyecta keyhook)
    ├── build_diag.py      # parchea RealSave.gba -> Diag0.gba (hook de prueba)
    ├── vpk0.py            # decodificador VPK0 (formato Nintendo, puerto de tehzz/vpk0)
    ├── rdis.py            # desensamblador Thumb con resolución de literales PC-relativos
    ├── comp.py            # compone los 4 BG en una imagen 240x160
    ├── comp2.py           # compone cada BG por separado
    ├── _ss.py             # descomprime el chunk gbAs de un savestate de mGBA a RAM cruda
    ├── _mapa.py           # renderiza el mapa completo de BG1 (hojas | flores) desde RAM
    ├── _shot.py           # captura la ventana de mGBA (la trae al frente y recorta)
    ├── _savestate.py      # manda Shift+F<n> a mGBA para guardar un savestate
    ├── _tcpsrv.py         # servidor TCP loopback de prueba (sanidad de red)
    ├── test_keyhook.py    # test unitario del hook con Unicorn (ARM Thumb)
    └── gdb/               # 18 recetas .txt para el stub GDB de mGBA (ver abajo)
```

---

## Hallazgos clave

El menú de Pikmin **no dibuja** la flor; **selecciona** entre dos copias
pre-cocinadas en el tilemap de BG1:

- Mapa de BG1 en EWRAM en `0x020380A4` (64×32 tiles = 4096 B); char data en
  `0x02004000`.
- El mapa tiene **dos copias horizontales**: tx 0–31 = hojas
  (`0x2026`/`0x2027`, paleta 2), tx 32–63 = flores (`0x2028`/`0x2029`).
  La ventana visible son 32 columnas (`B1HOFS=4`, `B1VOFS=0x1FF`).
- Por tanto el "estado de flor" por nivel se reduce a **un byte por celda**
  que elige qué copia apunta cada casilla.
- Selector de celda (el byte bandera que queremos localizar):
  `0x08022CF0` `ldrb r1,[r1]` → índice → tabla `0x084DF37C` → función de
  dibujo → `bl 0x080544B4`.
- DMA a VRAM: rutina `0x080036C0`; tabla de descriptores en `0x02032AA0`
  (16 B/entrada). SADs reales: BG0=`0x02037098`, BG1=`0x020380A4`,
  BG2=`0x020390B0`.
- Trampolín que desempaqueta el descriptor de 8 B: `0x08025FE8`.
- Stub de escaneo de ficha (donde se clavó el hook): `0x08740C00`; el wrapper
  que apaga/restaura IME está en `0x08740CA1`; el literal que lo llama está en
  `0x090B0` (apunta originalmente a `0x08740CA1`). El stub hace SIEMPRE
  `cursor = cursor + 1` (`0x08740C14`/`0x08740C16`), de ahí que el hook
  escriba `delta = deseado - 1`.

**Estado pendiente:** el valor/dirección exacta del array de bytes
"nivel completado" (flor) aún no está confirmado. Requiere un savestate en el
que la flor sea **visible** (menú en reposo, no a mitad de transición) para
hacer un diff contra el estado de solo-hojas. Una vez localizado, el plan de
persistencia es escribir en la flash libre del e-Reader
(`0x00000–0x0CFFF`, ~52 KB) en el stub de escaneo.

---

## Cómo usar las herramientas

### Hook de selección de ficha (`keyhook.s` / `keyhook.bin`)

ASM Thumb original. Compilar con devkitARM (`arm-none-eabi-as`). Se inyecta en
`0x08740D00` y se redirige el literal de `0x090B0` a `0x08740D01`.

Comportamiento (corre antes del stub de escaneo, que siempre suma +1):

| Tecla                | Efecto                  |
|----------------------|-------------------------|
| L / Izquierda        | ficha anterior (−1)     |
| R / Derecha          | ficha siguiente (+1)    |
| B+L / B+Izquierda    | −10 fichas              |
| B+R / B+Derecha      | +10 fichas              |
| A / Start / Select   | escanear y avanzar 1    |

`test_keyhook.py` lo valida bajo Unicorn midiendo el **efecto neto**
(hook + el +1 incondicional del stub).

### Parchear el ROM (`build_select.py`, `build_diag.py`)

```bash
# requiere Pikmin72_RealSave.gba y keyhook.bin/keyhook_diag.bin en el cwd
python tools/build_select.py   # -> Pikmin72_Select.gba
python tools/build_diag.py     # -> Pikmin72_Diag0.gba
```

> Estos scripts **no** traen el ROM base (ver aviso legal). Apórtalo tú.

### RE / análisis

```bash
python tools/rdis.py            # desensambla el ROM (edita la ruta al inicio)
python tools/vpk0.py <in> <out> # descomprime un blob VPK0 (si aplica)
python tools/_ss.py state.ss1 ram.bin   # savestate mGBA -> RAM cruda
python tools/_mapa.py ram.bin out.png   # render del mapa BG1 hojas|flores
python tools/comp.py            # compone los BG desde ram_dump.bin + vram_ss.bin
python tools/comp2.py           # lo mismo, un BG por archivo
```

`_shot.py` y `_savestate.py` controlan mGBA por ventana (solo Windows) para
capturar pantallas y guardar estados durante la sesión de depuración.

### Recetas GDB (`tools/gdb/`)

Son secuencias de comandos para el stub GDB de mGBA (`target remote
localhost:2345`). Ejemplos:

- `gdb8.txt`  — watch en `*(unsigned short*)0x0600D102` (escritura de tile).
- `gdb14.txt` — vuelca `map_bg1.bin` / `chr_bg1.bin` en el bp de `0x080036C0`.
- `gdb15.txt` — watch condicional `0x020382A6==0x2026` para cazar el dibujo
  de hoja en `0x080031C8`.
- `gdb16.txt` — vuelca la pila en el dibujo → cadena de retorno.
- `gdb17.txt` — break en `0x08022CF0`, lee el byte por celda + tabla
  `0x084DF37C`.
- `gdb18.txt` — watch `0x0200000C` → demostró que es cabecera de heap, no el
  índice.

---

## Trampas del entorno (Windows, este PC)

Documentadas para no volver a perder tiempo:

1. **El stub GDB de mGBA acepta UNA sola conexión por lanzamiento.** Si
   `target remote` falla o se corta, **relanza mGBA**; un segundo intento
   cuelga para siempre. El puerto tarda 1–2 s en escuchar: no conectes antes.
2. **Lanza mGBA desde bash en segundo plano**, no desde PowerShell. El mGBA
   lanzado por PowerShell es invisible para `EnumWindows` y su loopback TCP
   falla (Windows Network Isolation).
3. `curl` hereda `http_proxy`/`https_proxy` del entorno; usa
   `curl --noproxy '*'` contra servidores locales.
4. El `make` de este PC no hereda variables de entorno: pásalas como argumento
   (`make VAR=valor`).

---

## Licencia

MIT — ver `LICENSE`. El código aquí es original; el contenido con derechos de
autor (ROM, fichas) no se incluye.
