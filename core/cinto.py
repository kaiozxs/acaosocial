"""Desenho da faixa de jiu-jitsu (tecido, costuras, barra preta e listras) em PNG."""
import io
import math
from functools import lru_cache

from PIL import Image, ImageChops, ImageDraw, ImageFilter

CORES = {
    "branca": (242, 242, 240), "cinza": (150, 150, 152), "amarela": (244, 194, 13), "laranja": (240, 138, 36),
    "verde": (46, 158, 79), "azul": (31, 79, 196), "roxa": (122, 59, 194), "marrom": (107, 63, 29), "preta": (22, 22, 24),
}
W, H, M = 1800, 200, 40  # comprimento, altura e margem para a sombra


def _tom(cor, f):
    return tuple(max(0, min(255, int(c * f))) for c in cor)


def _gradiente_vertical(w, h, cor):
    img = Image.new("RGB", (w, h))
    px = img.load()
    for y in range(h):
        t = y / (h - 1)
        # luz suave no alto, escurece nas bordas: cilindro de tecido
        f = 0.80 + 0.30 * math.sin(math.pi * min(1, max(0, t * 0.9 + 0.05)))
        for x in range(w):
            px[x, y] = _tom(cor, f)
    return img


def _tecido(w, h):
    """Textura de trama bem sutil."""
    tex = Image.new("L", (w, h), 128)
    d = ImageDraw.Draw(tex)
    for x in range(-h, w, 7):
        d.line([(x, 0), (x + h, h)], fill=140, width=2)
    for y in range(0, h, 5):
        d.line([(0, y), (w, y)], fill=118, width=1)
    return tex.filter(ImageFilter.GaussianBlur(0.6))


def _faixa_base(cor, w=W, h=H):
    base = _gradiente_vertical(w, h, cor)
    tex = _tecido(w, h)
    base = ImageChops.multiply(base, Image.merge("RGB", (tex, tex, tex)).point(lambda v: 205 + int((v - 128) * .45)))
    base = base.point(lambda v: min(255, int(v * 1.18)))
    d = ImageDraw.Draw(base)
    escuro = _tom(cor, .62) if sum(cor) > 120 else (60, 60, 64)
    claro = _tom(cor, 1.35) if sum(cor) > 120 else (74, 74, 78)
    for fr in (.20, .36, .52, .68, .84):
        y = int(h * fr)
        d.line([(0, y), (w, y)], fill=escuro, width=3)
        d.line([(0, y + 3), (w, y + 3)], fill=claro, width=2)
    return base


def _barra(cor_barra, grau, h=H):
    bw = 330
    barra = _gradiente_vertical(bw, h, cor_barra)
    d = ImageDraw.Draw(barra)
    sombra = _tom(cor_barra, .6) if sum(cor_barra) > 120 else (50, 50, 54)
    for fr in (.20, .36, .52, .68, .84):
        y = int(h * fr)
        d.line([(0, y), (bw, y)], fill=sombra, width=3)
    # listras brancas (fitas)
    n = max(0, min(4, int(grau)))
    for i in range(n):
        x0 = 44 + i * 70
        fita = _gradiente_vertical(34, h, (246, 246, 244))
        barra.paste(fita, (x0, 0))
        d.line([(x0, 0), (x0, h)], fill=(190, 190, 188), width=2)
        d.line([(x0 + 33, 0), (x0 + 33, h)], fill=(170, 170, 168), width=2)
    return barra


@lru_cache(maxsize=64)
def faixa_png(chave, grau):
    cor = CORES.get(chave, (90, 90, 90))
    cor_barra = (200, 16, 46) if chave == "preta" else (14, 14, 16)
    base = _faixa_base(cor)
    barra = _barra(cor_barra, grau)
    x_barra = int(W * 0.70)
    base.paste(barra, (x_barra, 0))
    # bordas e sombra entre barra e faixa
    sombra = Image.new("L", (W, H), 0)
    ImageDraw.Draw(sombra).rectangle((x_barra - 6, 0, x_barra, H), fill=110)
    ImageDraw.Draw(sombra).rectangle((x_barra + 330, 0, x_barra + 336, H), fill=110)
    sombra = sombra.filter(ImageFilter.GaussianBlur(4))
    base = Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), base, sombra.point(lambda v: v // 2))
    # máscara com cantos arredondados nas pontas
    mascara = Image.new("L", (W * 2, H * 2), 0)
    ImageDraw.Draw(mascara).rounded_rectangle((0, 0, W * 2 - 1, H * 2 - 1), radius=26, fill=255)
    mascara = mascara.resize((W, H), Image.LANCZOS)
    tela = Image.new("RGBA", (W + 2 * M, H + 2 * M), (0, 0, 0, 0))
    # sombra projetada
    proj = Image.new("L", tela.size, 0)
    proj.paste(mascara, (M, M + 14))
    proj = proj.filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * .55))
    sombra_rgba = Image.new("RGBA", tela.size, (0, 0, 0, 0))
    sombra_rgba.putalpha(proj)
    tela = Image.alpha_composite(tela, sombra_rgba)
    faixa = base.convert("RGBA")
    faixa.putalpha(mascara)
    tela.alpha_composite(faixa, (M, M))
    # brilho de borda superior
    brilho = Image.new("RGBA", tela.size, (0, 0, 0, 0))
    ImageDraw.Draw(brilho).rounded_rectangle((M + 2, M + 2, M + W - 3, M + H - 3), radius=24, outline=(255, 255, 255, 38), width=3)
    tela = Image.alpha_composite(tela, brilho)
    saida = io.BytesIO()
    tela.save(saida, "PNG", optimize=True)
    return saida.getvalue()


def proporcao():
    return (W + 2 * M) / (H + 2 * M)
