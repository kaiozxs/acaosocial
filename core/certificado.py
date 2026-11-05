"""Geração do certificado de graduação em PDF (reportlab).

Papel creme, moldura azul e dourada, nome em letra cursiva, faixa desenhada com a
medalha do Icon na ponta, selo de cera azul e a logo do Projeto Salvação no topo.
"""
import base64
import io
import math

from django.conf import settings
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho",
         "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
COR_FAIXA = {
    "branca": "#f4f4f4", "cinza": "#9a9a9a", "amarela": "#f4c20d", "laranja": "#f08a24",
    "verde": "#2e9e4f", "azul": "#1f4fc4", "roxa": "#7a3bc2", "marrom": "#6b3f1d", "preta": "#111111",
}
PAPEL = HexColor("#f8f2e3")
AZUL = HexColor("#1f3a7a")
AZUL_CLARO = HexColor("#4a64a5")
OURO = HexColor("#b88a2e")
OURO_ESC = HexColor("#8a6417")
TINTA = HexColor("#2a2418")

_FONTES = settings.BASE_DIR / "static" / "fonts"
try:
    pdfmetrics.registerFont(TTFont("Cursiva", str(_FONTES / "GreatVibes-Regular.ttf")))
    pdfmetrics.registerFont(TTFont("Titulo", str(_FONTES / "Cinzel-Variable.ttf")))
    F_NOME, F_TITULO = "Cursiva", "Titulo"
except Exception:  # sem as fontes, cai para as padrão do PDF
    F_NOME, F_TITULO = "Times-BoldItalic", "Times-Bold"


def data_por_extenso(d):
    return f"{d.day} de {MESES[d.month - 1]} de {d.year}"


def _img(nome):
    caminho = settings.BASE_DIR / "static" / "img" / nome
    return ImageReader(str(caminho)) if caminho.exists() else None


def _texto_espacado(c, x, y, txt, fonte, tam, espaco, cor, grosso=0.0):
    """Texto centralizado em x com espaçamento entre letras."""
    larg = c.stringWidth(txt, fonte, tam) + espaco * (len(txt) - 1)
    c.saveState()
    t = c.beginText(x - larg / 2, y)
    t.setFont(fonte, tam)
    t.setCharSpace(espaco)
    t.setFillColor(cor)
    if grosso:
        t.setStrokeColor(cor)
        c.setLineWidth(grosso)
        t.setTextRenderMode(2)
    t.textOut(txt)
    c.drawText(t)
    c.restoreState()


def _moldura(c, W, H):
    # faixa azul externa
    c.setStrokeColor(AZUL); c.setLineWidth(10); c.rect(24, 24, W - 48, H - 48)
    c.setStrokeColor(OURO); c.setLineWidth(1.4); c.rect(33, 33, W - 66, H - 66)
    # corda decorativa
    c.setStrokeColor(AZUL); c.setLineWidth(13); c.rect(43, 43, W - 86, H - 86)
    c.setStrokeColor(HexColor("#d9c58a")); c.setLineWidth(1.2)
    x0, y0, x1, y1 = 36.5, 36.5, W - 36.5, H - 36.5
    passo = 6
    x = x0
    while x < x1 - 7:
        c.line(x, y0, x + 6, y0 + 13); c.line(x, y1 - 13, x + 6, y1)
        x += passo
    y = y0
    while y < y1 - 7:
        c.line(x0, y, x0 + 13, y + 6); c.line(x1 - 13, y, x1, y + 6)
        y += passo
    c.setStrokeColor(OURO); c.setLineWidth(1.2); c.rect(53, 53, W - 106, H - 106)
    c.setStrokeColor(AZUL_CLARO); c.setLineWidth(.7); c.rect(57, 57, W - 114, H - 114)
    # volutas douradas nos cantos
    c.setStrokeColor(OURO); c.setFillColor(OURO)
    for (cx, cy, ini) in ((57, H - 57, 270), (W - 57, H - 57, 180), (57, 57, 0), (W - 57, 57, 90)):
        for r, lw in ((16, 1.4), (27, 1.0), (38, .7)):
            c.setLineWidth(lw)
            c.arc(cx - r, cy - r, cx + r, cy + r, ini, 90)
        c.circle(cx, cy, 3, fill=1, stroke=0)


def _faixa(c, cx, y, chave, grau, largura=340, altura=28):
    x = cx - largura / 2
    c.setFillColor(HexColor(COR_FAIXA.get(chave, "#444")))
    c.setStrokeColor(HexColor("#55575f")); c.setLineWidth(.9)
    c.rect(x, y, largura, altura, fill=1, stroke=1)
    # costuras
    c.setStrokeColor(HexColor("#00000033") if chave != "branca" else HexColor("#c9c9c9")); c.setLineWidth(.5)
    for dy in (6, altura - 6):
        c.line(x + 4, y + dy, x + largura - 4, y + dy)
    # barra dos graus
    bw = 78
    bx = x + largura - bw - 40
    c.setFillColor(HexColor("#c8102e") if chave == "preta" else black)
    c.rect(bx, y, bw, altura, fill=1, stroke=0)
    c.setFillColor(white)
    for i in range(min(int(grau), 4)):
        c.rect(bx + 9 + i * 16, y + 3, 6, altura - 6, fill=1, stroke=0)
    return x + largura  # extremidade direita


def _medalha(c, cx, cy, r=25):
    c.setFillColor(HexColor("#00000022")); c.circle(cx + 1.5, cy - 2, r + 1, fill=1, stroke=0)
    c.setFillColor(OURO); c.circle(cx, cy, r, fill=1, stroke=0)
    c.setFillColor(HexColor("#f3d98b")); c.circle(cx, cy, r - 3, fill=1, stroke=0)
    c.setFillColor(white); c.circle(cx, cy, r - 6, fill=1, stroke=0)
    icone = _img("icon.png")
    if icone:
        lado = (r - 6) * 1.55
        c.drawImage(icone, cx - lado / 2, cy - lado / 2, lado, lado, mask="auto")


def _selo(c, cx, cy, r=31):
    c.setFillColor(HexColor("#00000030")); c.circle(cx + 2, cy - 3, r, fill=1, stroke=0)
    c.setFillColor(AZUL)
    for i in range(0, 360, 12):
        a = math.radians(i)
        c.circle(cx + (r - 4) * math.cos(a), cy + (r - 4) * math.sin(a), 6, fill=1, stroke=0)
    c.circle(cx, cy, r - 4, fill=1, stroke=0)
    c.setStrokeColor(AZUL_CLARO); c.setLineWidth(1.6); c.circle(cx, cy, r - 10, fill=0, stroke=1)
    c.setStrokeColor(HexColor("#2c4d9c")); c.setLineWidth(1); c.circle(cx, cy, r - 7, fill=0, stroke=1)
    icone = _img("icon.png")
    if icone:
        lado = (r - 11) * 1.5
        c.drawImage(icone, cx - lado / 2, cy - lado / 2, lado, lado, mask="auto")


def gerar(nome, faixa_chave, faixa_nome, grau, data, prof_nome, prof_titulo, assinatura_b64=""):
    buf = io.BytesIO()
    W, H = landscape(A4)
    c = canvas.Canvas(buf, pagesize=(W, H))
    c.setTitle(f"Certificado - {nome}")
    c.setFillColor(PAPEL); c.rect(0, 0, W, H, fill=1, stroke=0)
    _moldura(c, W, H)
    cx = W / 2

    # logo do Projeto Salvação no topo
    logo = _img("logo-projeto.png")
    if logo:
        c.setFillColor(white); c.circle(cx, H - 100, 40, fill=1, stroke=0)
        c.drawImage(logo, cx - 36, H - 136, 72, 72, mask="auto")
        c.setStrokeColor(OURO); c.setLineWidth(2.4); c.circle(cx, H - 100, 38.5, fill=0, stroke=1)

    _texto_espacado(c, cx, H - 170, "CERTIFICADO DE GRADUAÇÃO", F_TITULO, 27, 1.6, OURO, grosso=.5)
    c.setFillColor(TINTA); c.setFont("Times-Roman", 12.5)
    c.drawCentredString(cx, H - 192, "Certificamos que")

    tam = 50
    while c.stringWidth(nome, F_NOME, tam) > W - 260 and tam > 22:
        tam -= 2
    c.setFillColor(OURO_ESC); c.setFont(F_NOME, tam)
    c.drawCentredString(cx, H - 236, nome)
    nw = min(c.stringWidth(nome, F_NOME, tam) + 70, W - 200)
    c.setStrokeColor(OURO); c.setLineWidth(.9); c.line(cx - nw / 2, H - 246, cx + nw / 2, H - 246)

    c.setFillColor(TINTA); c.setFont("Times-Roman", 13)
    c.drawCentredString(cx, H - 270, "concluiu com dedicação e disciplina o seu período de treinos e foi graduado(a) à")

    ponta = _faixa(c, cx - 14, H - 338, faixa_chave, grau)
    _medalha(c, ponta + 4, H - 338 + 14)

    rotulo = f"Faixa {faixa_nome}" + (f" · {grau}º grau" if int(grau) else "")
    _texto_espacado(c, cx, H - 378, rotulo, F_TITULO, 16, .8, TINTA, grosso=.35)
    c.setFillColor(TINTA); c.setFont("Times-Roman", 12.5)
    c.drawCentredString(cx, H - 399, f"em {data_por_extenso(data)}, no CT Salvação — Projeto Salvação.")

    # assinatura (à esquerda do selo)
    sx, ay = cx - 105, 112
    if assinatura_b64:
        try:
            raw = base64.b64decode(assinatura_b64.split(",")[-1])
            img = ImageReader(io.BytesIO(raw))
            iw, ih = img.getSize()
            esc = min(180 / iw, 54 / ih)
            c.drawImage(img, sx - iw * esc / 2, ay + 2, iw * esc, ih * esc, mask="auto")
        except Exception:
            pass
    c.setStrokeColor(TINTA); c.setLineWidth(.8); c.line(sx - 105, ay, sx + 105, ay)
    c.setFillColor(TINTA); c.setFont("Times-Bold", 13)
    c.drawCentredString(sx, ay - 15, prof_nome)
    c.setFont("Times-Roman", 9.5)
    c.drawCentredString(sx, ay - 27, prof_titulo)

    _selo(c, cx + 135, 100)
    c.showPage()
    c.save()
    return buf.getvalue()
