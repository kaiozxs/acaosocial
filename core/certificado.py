"""Geração do certificado de graduação em PDF (reportlab)."""
import base64
import io

from django.conf import settings
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho",
         "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
COR_FAIXA = {
    "branca": "#f4f4f4", "cinza": "#9a9a9a", "amarela": "#f4c20d", "laranja": "#f08a24",
    "verde": "#2e9e4f", "azul": "#2457d6", "roxa": "#7a3bc2", "marrom": "#6b3f1d", "preta": "#111111",
}
VERM = HexColor("#c8102e")
PAPEL = HexColor("#f6f1e4")


def data_por_extenso(d):
    return f"{d.day} de {MESES[d.month - 1]} de {d.year}"


def _faixa(c, cx, y, chave, grau, largura=300, altura=30):
    x = cx - largura / 2
    c.setFillColor(HexColor(COR_FAIXA.get(chave, "#444")))
    c.setStrokeColor(HexColor("#555"))
    c.setLineWidth(1)
    c.rect(x, y, largura, altura, fill=1, stroke=1)
    barra_w = 70
    bx = x + largura - barra_w - 28
    c.setFillColor(VERM if chave == "preta" else black)
    c.rect(bx, y, barra_w, altura, fill=1, stroke=0)
    c.setFillColor(white)
    for i in range(min(int(grau), 4)):
        c.rect(bx + 10 + i * 13, y + 3, 5, altura - 6, fill=1, stroke=0)
    c.setFillColor(black)


def gerar(nome, faixa_chave, faixa_nome, grau, data, prof_nome, prof_titulo, assinatura_b64=""):
    buf = io.BytesIO()
    W, H = landscape(A4)
    c = canvas.Canvas(buf, pagesize=(W, H))
    c.setTitle(f"Certificado - {nome}")
    c.setFillColor(PAPEL)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    # molduras
    c.setStrokeColor(black); c.setLineWidth(4); c.rect(22, 22, W - 44, H - 44)
    c.setStrokeColor(VERM); c.setLineWidth(1.6); c.rect(32, 32, W - 64, H - 64)
    c.setFillColor(black)
    for (px, py) in ((22, 22), (W - 22, 22), (22, H - 22), (W - 22, H - 22)):
        c.circle(px, py, 7, fill=1, stroke=0)
    # logo
    logo = settings.BASE_DIR / "static" / "img" / "logo.png"
    if logo.exists():
        c.drawImage(ImageReader(str(logo)), W / 2 - 38, H - 125, 76, 76, mask="auto")
    # título
    c.setFillColor(black)
    c.setFont("Times-Bold", 34)
    c.drawCentredString(W / 2, H - 165, "CERTIFICADO DE GRADUAÇÃO")
    c.setStrokeColor(VERM); c.setLineWidth(2.2)
    c.line(W / 2 - 90, H - 177, W / 2 + 90, H - 177)
    c.setFont("Times-Roman", 15)
    c.drawCentredString(W / 2, H - 205, "Certificamos que")
    # nome
    tam = 36
    while c.stringWidth(nome, "Times-BoldItalic", tam) > W - 190 and tam > 18:
        tam -= 2
    c.setFont("Times-BoldItalic", tam)
    c.drawCentredString(W / 2, H - 248, nome)
    nw = min(c.stringWidth(nome, "Times-BoldItalic", tam) + 40, W - 150)
    c.setStrokeColor(black); c.setLineWidth(.8)
    c.line(W / 2 - nw / 2, H - 257, W / 2 + nw / 2, H - 257)
    # texto
    c.setFont("Times-Roman", 15)
    c.drawCentredString(W / 2, H - 285, "concluiu com dedicação e disciplina o seu período de treinos e foi graduado(a) à")
    _faixa(c, W / 2, H - 350, faixa_chave, grau)
    rotulo = f"Faixa {faixa_nome}" + (f" · {grau}º grau" if int(grau) else "")
    c.setFont("Times-Bold", 20)
    c.drawCentredString(W / 2, H - 384, rotulo)
    c.setFont("Times-Roman", 14)
    c.drawCentredString(W / 2, H - 412, f"em {data_por_extenso(data)}, no CT Salvação — Projeto Salvação.")
    # assinatura
    ay = 98
    if assinatura_b64:
        try:
            raw = base64.b64decode(assinatura_b64.split(",")[-1])
            img = ImageReader(io.BytesIO(raw))
            iw, ih = img.getSize()
            esc = min(190 / iw, 62 / ih)
            c.drawImage(img, W / 2 - iw * esc / 2, ay + 2, iw * esc, ih * esc, mask="auto")
        except Exception:
            pass
    c.setStrokeColor(black); c.setLineWidth(.8)
    c.line(W / 2 - 120, ay, W / 2 + 120, ay)
    c.setFont("Times-Bold", 14)
    c.drawCentredString(W / 2, ay - 16, prof_nome)
    c.setFont("Times-Roman", 10)
    c.drawCentredString(W / 2, ay - 29, prof_titulo)
    c.showPage()
    c.save()
    return buf.getvalue()
