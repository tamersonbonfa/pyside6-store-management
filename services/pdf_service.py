from __future__ import annotations
from pathlib import Path
from typing import Any
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from config import NOME_LOJA, VERSAO_SISTEMA

APP_NAME = NOME_LOJA

def _money(centavos: int | None) -> str:
    try:
        reais = centavos / 100
        return f"R$ {reais:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"

def gerar_recibo_80mm(dados: dict[str, Any]) -> str:
    venda = dados["venda"]
    itens = dados["itens"]

    w = 80 * mm
    h = (130 + len(itens) * 18) * mm / 3.0
    if h < 150 * mm: h = 150 * mm

    out_dir = Path("recibos")
    out_dir.mkdir(parents=True, exist_ok=True)
    venda_id = int(venda["id"])
    filename = out_dir / f"recibo_{venda_id}.pdf"

    c = canvas.Canvas(str(filename), pagesize=(w, h))
    y = h - 10 * mm

    def line(txt: str, size=9, bold=False):
        nonlocal y
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        c.drawString(6 * mm, y, txt)
        y -= 5 * mm

    # Logo
    logo_path = Path("assets") / "logo.png"
    if logo_path.exists():
        try:
            c.drawImage(str(logo_path), 20 * mm, y - 18 * mm, width=40 * mm, height=18 * mm, preserveAspectRatio=True)
            y -= 22 * mm
        except: pass

    line(APP_NAME, size=12, bold=True)
    line("Recibo de Venda", size=10, bold=True)
    line("-" * 38)
    line(f"Venda: #{venda_id}", bold=True)
    line(f"Data: {venda.get('data', '')}")
    line(f"Pagamento: {venda.get('forma_pagamento', '')}")
    line(f"Vendedor: {venda.get('usuario_nome', 'Desconhecido')}") # Exibição corrigida
    line("-" * 38)

    # Cliente
    line("Cliente: " + (venda.get("cliente_nome") or "Consumidor"), bold=True)
    line("-" * 38)

    # Itens
    line("Itens:", bold=True)
    total_desconto_centavos = 0

    for it in itens:
        nome = it.get("produto_nome") or ""
        qtd = int(it.get("quantidade") or 0)
        preco = int(it.get("preco_unitario_centavos") or 0)
        subtotal = int(it.get("subtotal_centavos") or 0)
        desc_perc = float(it.get("desconto") or 0)

        # Cálculo do desconto em R$ para o rodapé
        total_desconto_centavos += int(
            (qtd * preco) * (desc_perc / 100)
        )

        titulo = f"{nome} ({it.get('produto_marca','')})"[:34]
        line(titulo, bold=True)
        line(f"{qtd} x {_money(preco)} = {_money(subtotal)} (Desc: {desc_perc:.0f}%)")
        y -= 2 * mm

    line("-" * 38)
    line(f"TOTAL: {_money(venda.get('total_centavos', 0))}", size=11, bold=True)
    if total_desconto_centavos > 0:
        line(f"Desconto aplicado: {_money(total_desconto_centavos)}")
    line(f"Pago: {_money(venda.get('valor_pago_centavos', 0))}")
    line(f"Troco: {_money(venda.get('troco_centavos', 0))}")

    obs = (venda.get("observacoes") or "").strip()
    if obs:
        line("-" * 38)
        line("Obs:", bold=True)
        for chunk in [obs[i:i+36] for i in range(0, len(obs), 36)]:
            line(chunk)

    line("-" * 38)
    line("Obrigado pela preferência!", bold=True)
    c.showPage()
    c.save()
    return str(filename)