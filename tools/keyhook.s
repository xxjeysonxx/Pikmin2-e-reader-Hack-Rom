    .syntax unified
    .thumb
    .text
    .global keyhook
    .thumb_func

@ Hook de seleccion de ficha para Card e-Reader+ (JPN, PSAJ/ERDJ).
@
@ Corre ANTES del stub de escaneo, que hace SIEMPRE cursor = cursor + 1
@ (0x08740C14: adds r3,r1,#1 / 0x08740C16: str r3,[r0]).
@ Por tanto el hook escribe  delta = deseado - 1.
@
@ COMPORTAMIENTO: no escanea solo. Se queda bloqueado hasta que pulses.
@   1) Espera a que NO haya ninguna tecla de disparo pulsada. Esto evita que
@      una tecla que ya venias manteniendo (p.ej. la direccion con la que
@      andabas, o el A con el que cerraste la pantalla anterior) dispare el
@      escaneo nada mas llegar.
@   2) Espera a que pulses una tecla de disparo.
@   3) Aplica el delta segun lo que tengas pulsado.
@
@   L / Izquierda         -> ficha anterior (-1)
@   R / Derecha           -> ficha siguiente (+1)
@   B + L / B + Izquierda -> -10 fichas
@   B + R / B + Derecha   -> +10 fichas
@   A / Start / Select    -> escanear y avanzar 1 (comportamiento original)
@   B solo, arriba, abajo -> NO disparan (B es modificador)
@
@ Solo usa r0-r3: el wrapper del stub salva r4-r6 y lr, asi que r4+ son
@ callee-saved y no se pueden tocar aqui. IME/IE no se tocan: el wrapper que
@ viene despues ya los apaga y los restaura.
@
@ NOTA: no asumir que "nada pulsado" es 0x03FF. En algunos modelos los bits
@ 10-15 de KEYINPUT leen 1, por eso siempre se enmascara con TRIGMASK antes
@ de comparar.

.equ KEYINPUT,  0x04000130
.equ CURSOR,    0x0202F8A0
.equ WRAPPER,   0x08740CA1
.equ NCARDS,    72
@ bits A(0) | Select(2) | Start(3) | Derecha(4) | Izquierda(5) | R(8) | L(9)
.equ TRIGMASK,  0x033D

keyhook:
    ldr     r0, =KEYINPUT
    ldr     r2, =TRIGMASK

    @ 1) esperar a que se suelte todo (tecla venia mantenida)
.Lrelease:
    ldrh    r3, [r0]
    ands    r3, r3, r2
    cmp     r3, r2
    bne     .Lrelease               @ algo pulsado -> seguir esperando a que suelte

    @ 2) esperar a que se pulse algo
.Lpress:
    ldrh    r3, [r0]
    ands    r3, r3, r2
    cmp     r3, r2
    bne     .Lgot
    b       .Lpress

.Lgot:
    ldrh    r1, [r0]                @ r1 = teclas

    @ paso = 1 ; con B pulsado, paso = 10
    movs    r3, #1
    movs    r2, #0x02               @ B = bit 1
    tst     r1, r2
    bne     .Lstep_ready
    movs    r3, #10
.Lstep_ready:

    @ izquierda: cruceta bit 5
    movs    r2, #0x20
    tst     r1, r2
    beq     .Lneg
    @ izquierda: L = bit 9
    movs    r2, #0x02
    lsls    r2, r2, #8              @ 0x0200
    tst     r1, r2
    beq     .Lneg

    @ derecha: cruceta bit 4
    movs    r2, #0x10
    tst     r1, r2
    beq     .Lpos
    @ derecha: R = bit 8
    movs    r2, #0x01
    lsls    r2, r2, #8              @ 0x0100
    tst     r1, r2
    beq     .Lpos

    @ A / Start / Select: avance normal de 1
    movs    r3, #0
    b       .Lapply

.Lneg:
    rsbs    r3, r3, #0              @ r3 = -paso
    subs    r3, r3, #1              @ delta = -(paso+1)
    b       .Lapply

.Lpos:
    subs    r3, r3, #1              @ delta = paso-1

.Lapply:
    ldr     r0, =CURSOR
    ldr     r2, [r0]
    adds    r2, r2, r3
    bpl     .Lwrap_hi
    adds    r2, r2, #NCARDS         @ envolver por abajo
    b       .Lstore
.Lwrap_hi:
    cmp     r2, #NCARDS
    blo     .Lstore
    subs    r2, r2, #NCARDS         @ envolver por arriba
.Lstore:
    str     r2, [r0]

.Ldone:
    ldr     r0, =WRAPPER
    bx      r0

    .ltorg
