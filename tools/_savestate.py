"""Trae mGBA al frente y le manda Shift+F<n> para guardar savestate.

Uso: python _savestate.py <n>     (n = 1..9, slot destino)
"""
import ctypes
import ctypes.wintypes as wt
import sys
import time

u = ctypes.windll.user32

VK_SHIFT = 0x10
VK_F1 = 0x70


def ventana_mgba():
    encontradas = []

    def cb(h, l):
        if not u.IsWindowVisible(h):
            return True
        n = u.GetWindowTextLengthW(h)
        if n <= 0:
            return True
        buf = ctypes.create_unicode_buffer(n + 1)
        u.GetWindowTextW(h, buf, n + 1)
        if buf.value.startswith("mGBA"):
            r = wt.RECT()
            u.GetWindowRect(h, ctypes.byref(r))
            encontradas.append((h, buf.value, r.right - r.left, r.bottom - r.top))
        return True

    CB = ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)
    u.EnumWindows(CB(cb), 0)
    return encontradas[0] if encontradas else None


def main():
    slot = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    w = ventana_mgba()
    if not w:
        print("no hay ventana de mGBA")
        return 1
    h, titulo, ancho, alto = w
    print("ventana:", titulo, ancho, "x", alto)
    u.SetForegroundWindow(h)
    time.sleep(0.5)
    vk = VK_F1 + (slot - 1)
    u.keybd_event(VK_SHIFT, 0, 0, 0)
    time.sleep(0.05)
    u.keybd_event(vk, 0, 0, 0)
    time.sleep(0.08)
    u.keybd_event(vk, 0, 2, 0)
    time.sleep(0.05)
    u.keybd_event(VK_SHIFT, 0, 2, 0)
    time.sleep(0.6)
    print("Shift+F%d enviado (slot %d)" % (slot, slot))
    return 0


if __name__ == "__main__":
    sys.exit(main())
