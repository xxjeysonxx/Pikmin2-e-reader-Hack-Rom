"""Captura la ventana de mGBA (la trae al frente y recorta su rectangulo).

Uso: python _shot.py salida.png
"""
import ctypes
import ctypes.wintypes as wt
import sys
import time

u = ctypes.windll.user32


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
            encontradas.append((h, buf.value, r.left, r.top, r.right, r.bottom))
        return True

    CB = ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)
    u.EnumWindows(CB(cb), 0)
    return encontradas[0] if encontradas else None


def main():
    salida = sys.argv[1] if len(sys.argv) > 1 else "_shot.png"
    w = ventana_mgba()
    if not w:
        print("no hay ventana de mGBA")
        return 1
    h, titulo, l, t, r, b = w
    u.SetForegroundWindow(h)
    time.sleep(0.6)
    from PIL import ImageGrab

    im = ImageGrab.grab(bbox=(l, t, r, b), all_screens=True)
    im.save(salida)
    print("guardado", salida, im.size, "|", titulo)
    return 0


if __name__ == "__main__":
    sys.exit(main())
