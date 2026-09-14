from __future__ import annotations

import os
import subprocess
import re
from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCompleter, QAbstractItemView, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QSpinBox, QDoubleSpinBox, QTableWidget, QTableWidgetItem,
    QMessageBox, QTextEdit
)

from services.vendas_service import (
    listar_produtos_ativos_para_venda,
    listar_clientes_para_venda,
    criar_venda,
    obter_dados_venda,
)
from services.pdf_service import gerar_recibo_80mm

def _money(v: float) -> str:
    try:
        return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"



def registrar_movimentacao_saida(produto_id: int, quantidade: int, venda_id: int, usuario_id: int, desconto: float = 0):
    """
    Registra saída de estoque apenas na finalização da venda, com usuário.
    """
    from database.db import get_connection

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        produto = conn.execute("SELECT tamanho, unidade FROM produtos WHERE id = ?", (produto_id,)).fetchone()
        tamanho = produto["tamanho"] if produto else 0
        unidade = produto["unidade"] if produto else "un"

        # Insere movimentação de saída
        conn.execute(
            """
            INSERT INTO movimentacoes_estoque
                (data, tipo, produto_id, quantidade, observacao, usuario_id, venda_id, tamanho, unidade)
            VALUES (?, 'SAIDA', ?, ?, ?, ?, ?, ?, ?)
            """,
            (now, produto_id, quantidade, f"Venda", usuario_id, venda_id, tamanho, unidade)
        )

        # Atualiza estoque
        conn.execute(
            "UPDATE produtos SET quantidade = quantidade - ? WHERE id = ?",
            (quantidade, produto_id)
        )
        conn.commit()


class TelaVendas(QWidget):
    def __init__(self, usuario_id: int):
        super().__init__()
        self.usuario_id = usuario_id
        self.produtos: list[dict] = []
        self.clientes: list[dict] = []
        self.carrinho: list[dict] = []

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # --- Título ---
        title_row = QHBoxLayout()
        title = QLabel("🧾 Vendas")
        title.setObjectName("Title")
        self.btn_refresh = QPushButton("🔄 Atualizar")
        title_row.addWidget(title, 1)
        title_row.addWidget(self.btn_refresh)
        layout.addLayout(title_row)

        # --- Cliente + pagamento ---
        top = QHBoxLayout()
        self.cb_cliente = QComboBox()
        self._make_searchable_combo(self.cb_cliente)
        self.cb_cliente.setMinimumWidth(380)

        self.cb_pag = QComboBox()
        self.cb_pag.addItems(["DINHEIRO", "PIX", "CARTAO", "CREDIARIO"])

        self.sp_pago = QDoubleSpinBox()
        self.sp_pago.setRange(0, 999999)
        self.sp_pago.setDecimals(2)

        top.addWidget(QLabel("Cliente:"))
        top.addWidget(self.cb_cliente, 1)
        top.addWidget(QLabel("Pagamento:"))
        top.addWidget(self.cb_pag)
        top.addWidget(QLabel("Valor pago:"))
        top.addWidget(self.sp_pago)
        layout.addLayout(top)

        # --- Código de barras ---
        barcode_row = QHBoxLayout()
        self.ed_barcode = QLineEdit()
        self.ed_barcode.setPlaceholderText("Bater código de barras e pressionar ENTER")
        barcode_row.addWidget(QLabel("Código de barras:"))
        barcode_row.addWidget(self.ed_barcode, 1)
        layout.addLayout(barcode_row)
        self.ed_barcode.returnPressed.connect(self.adicionar_por_codigo)

        # --- Produto + qtd + desconto ---
        row = QHBoxLayout()
        self.cb_produto = QComboBox()
        self._make_searchable_combo(self.cb_produto)
        self.cb_produto.setMinimumWidth(520)

        self.sp_qtd = QSpinBox()
        self.sp_qtd.setRange(1, 9999)
        self.sp_qtd.setValue(1)

        self.sp_desconto = QDoubleSpinBox()
        self.sp_desconto.setRange(0, 100)
        self.sp_desconto.setDecimals(2)
        self.sp_desconto.setSuffix("%")
        self.sp_desconto.setValue(0)

        self.btn_add = QPushButton("➕ Adicionar")
        self.btn_add.setObjectName("Primary")

        row.addWidget(QLabel("Produto:"))
        row.addWidget(self.cb_produto, 1)
        row.addWidget(QLabel("Qtd:"))
        row.addWidget(self.sp_qtd)
        row.addWidget(QLabel("Desconto:"))
        row.addWidget(self.sp_desconto)
        row.addWidget(self.btn_add)
        layout.addLayout(row)

        # --- Carrinho ---
        self.tbl = QTableWidget(0, 9)
        self.tbl.setHorizontalHeaderLabels([
            "ID", "Produto", "Tamanho", "Unidade", "Qtd", "Preço", "Desconto %", "Subtotal", "REMOVER"
        ])
        self.tbl.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl.setAlternatingRowColors(True)
        self.tbl.cellChanged.connect(self._on_cell_changed)
        layout.addWidget(self.tbl, 1)

        # --- Observações + total ---
        bottom = QHBoxLayout()
        self.ed_obs = QTextEdit()
        self.ed_obs.setPlaceholderText("Observações da venda (opcional)...")
        self.ed_obs.setFixedHeight(90)

        side = QVBoxLayout()
        self.lbl_total = QLabel("TOTAL: R$ 0,00")
        self.lbl_total.setStyleSheet("font-size: 18px; font-weight: 700;")
        self.lbl_troco = QLabel("Troco: R$ 0,00")
        self.lbl_troco.setStyleSheet("opacity: 0.85;")
        self.btn_finalizar = QPushButton("✅ Finalizar Venda")
        self.btn_finalizar.setObjectName("Primary")

        side.addWidget(self.lbl_total)
        side.addWidget(self.lbl_troco)
        side.addSpacing(8)
        side.addWidget(self.btn_finalizar)
        side.addStretch(1)

        bottom.addWidget(self.ed_obs, 1)
        bottom.addLayout(side)
        layout.addLayout(bottom)

        # --- Eventos ---
        self.btn_refresh.clicked.connect(self.carregar)
        self.btn_add.clicked.connect(self.adicionar_item)
        self.btn_finalizar.clicked.connect(self.finalizar)
        self.sp_pago.valueChanged.connect(self.atualizar_totais)
        self.cb_pag.currentTextChanged.connect(self.alterar_forma_pagamento)

        self.carregar()
    
    # Alterar forma pagamento
    def alterar_forma_pagamento(self, forma):
        forma = forma.upper()

        if forma == "CREDIARIO":
            self.sp_pago.setValue(0)
            self.sp_pago.setEnabled(True)
            self.lbl_troco.setText("Pagamento parcial ou total no crediário")
        else:
            self.sp_pago.setEnabled(True)
            self.atualizar_totais()

    # --- Auxiliares ---
    def _make_searchable_combo(self, combo):
        combo.setEditable(True)
        combo.setInsertPolicy(combo.InsertPolicy.NoInsert)
        combo.setMaxVisibleItems(20)
        completer = QCompleter(combo.model(), combo)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        combo.setCompleter(completer)
        combo.lineEdit().setPlaceholderText("Digite para pesquisar...")

    def _produto_by_id(self, pid: int) -> dict | None:
        return next((p for p in self.produtos if int(p["id"]) == pid), None)

    # --- Carregamento ---
    def carregar(self):
        from services.vendas_service import listar_produtos_ativos_para_venda, listar_clientes_para_venda

        self.produtos = listar_produtos_ativos_para_venda()
        self.clientes = listar_clientes_para_venda()

        # Clientes
        self.cb_cliente.clear()
        self.cb_cliente.addItem("SEM CLIENTE", None)
        for c in self.clientes:
            label = c["nome"]
            if c.get("telefone"):
                label += f" - {c['telefone']}"
            self.cb_cliente.addItem(label, int(c["id"]))

        # Produtos
        self.cb_produto.clear()
        for p in self.produtos:
            p["codigo_barras"] = str(p.get("codigo_barras") or "").strip()
            p["tamanho"] = p.get("tamanho") or p.get("volume_ml") or ""
            p["unidade"] = p.get("unidade") or ("ml" if p.get("volume_ml") else "")
            estoque = int(p.get("quantidade") or 0)
            preco = float(p.get("preco_venda") or 0)
            label = f"{p['nome']}"
            if p.get("marca"):
                label += f" ({p['marca']})"
            if p["tamanho"]:
                label += f" {p['tamanho']}{p['unidade']}"
            label += f" | Estoque: {estoque}"
            label += f" | {_money(preco)}"
            self.cb_produto.addItem(label, int(p["id"]))

        self.carrinho.clear()
        self.render_carrinho()
        self.atualizar_totais()

    # --- Adicionar produtos ---
    def adicionar_item(self):
        if self.cb_produto.currentIndex() < 0:
            return
        pid = int(self.cb_produto.currentData())
        qtd = int(self.sp_qtd.value())
        desconto = float(self.sp_desconto.value())
        self._adicionar_ao_carrinho(pid, qtd, desconto)

    def adicionar_por_codigo(self):
        codigo = self.ed_barcode.text().strip()
        if not codigo:
            return
        produto = None
        codigo_norm = re.sub(r'\W+', '', codigo).upper()
        for p in self.produtos:
            if (p.get("codigo_barras") or "").strip().upper() == codigo_norm:
                produto = p
                break
        if not produto:
            cod_num = ''.join(filter(str.isdigit, codigo))
            for p in self.produtos:
                cb_num = ''.join(filter(str.isdigit, str(p.get("codigo_barras") or "")))
                if cb_num == cod_num:
                    produto = p
                    break
        if not produto:
            QMessageBox.warning(self, "Erro", f"Produto com código '{codigo}' não encontrado.")
            self.ed_barcode.clear()
            return

        qtd = int(self.sp_qtd.value())
        desconto = float(self.sp_desconto.value())
        self._adicionar_ao_carrinho(int(produto["id"]), qtd, desconto)
        self.ed_barcode.clear()

    def _adicionar_ao_carrinho(self, pid: int, qtd: int, desconto: float):
        p = self._produto_by_id(pid)
        if not p:
            QMessageBox.warning(self, "Erro", "Produto não encontrado.")
            return
        estoque = int(p.get("quantidade", 0))
        preco = float(p.get("preco_venda", 0))
        if qtd > estoque:
            QMessageBox.warning(self, "Estoque insuficiente", f"Estoque atual: {estoque}")
            return
        if preco <= 0:
            QMessageBox.warning(self, "Aviso", "Produto sem preço de venda.")
            return

        # Apenas para exibir no combo, não altera estoque ainda
        estoque_estimado = estoque - qtd

        existente = next((it for it in self.carrinho if it["produto_id"] == pid), None)
        if existente:
            nova_qtd = existente["quantidade"] + qtd
            if nova_qtd > estoque:
                QMessageBox.warning(self, "Estoque insuficiente", f"Estoque atual: {estoque}")
                return
            existente["quantidade"] = nova_qtd
            existente["desconto"] = desconto
            existente["subtotal"] = nova_qtd * preco * (1 - desconto / 100)
        else:
            self.carrinho.append({
                "produto_id": pid,
                "nome": p["nome"],
                "tamanho": p.get("tamanho", ""),
                "unidade": p.get("unidade", ""),
                "quantidade": qtd,
                "preco_unitario": preco,
                "desconto": desconto,
                "subtotal": qtd * preco * (1 - desconto / 100),
            })
        self._atualizar_combo_produto_label(pid, estoque_estimado)
        self.render_carrinho()
        self.atualizar_totais()

    # --- Carrinho ---
    def render_carrinho(self):
        from PySide6.QtWidgets import QPushButton
        self.tbl.blockSignals(True)
        self.tbl.setRowCount(0)
        for it in self.carrinho:
            r = self.tbl.rowCount()
            self.tbl.insertRow(r)
            valores = [
                str(it["produto_id"]),
                it["nome"],
                str(it.get("tamanho", "")),
                it.get("unidade", ""),
                str(it["quantidade"]),
                _money(it["preco_unitario"]),
                str(it.get("desconto", 0)),
                _money(it["subtotal"]),
            ]
            for c, v in enumerate(valores):
                item = QTableWidgetItem(v)
                item.setTextAlignment(Qt.AlignCenter)
                if c in (4, 6):
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                else:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.tbl.setItem(r, c, item)
            btn_remover = QPushButton("🗑️")
            btn_remover.clicked.connect(lambda _, row=r: self._remover_item_por_linha(row))
            self.tbl.setCellWidget(r, 8, btn_remover)
        self.tbl.resizeColumnsToContents()
        self.tbl.blockSignals(False)

    def _remover_item_por_linha(self, row: int):
        if row < 0 or row >= len(self.carrinho):
            return
        pid = int(self.tbl.item(row, 0).text())
        item = next(it for it in self.carrinho if it["produto_id"] == pid)
        p = self._produto_by_id(pid)
        if p:
            self._atualizar_combo_produto_label(pid)
        self.carrinho = [it for it in self.carrinho if it["produto_id"] != pid]
        self.render_carrinho()
        self.atualizar_totais()

    def _atualizar_combo_produto_label(self, pid: int, estoque_estimado: int | None = None):
        for i in range(self.cb_produto.count()):
            if self.cb_produto.itemData(i) == pid:
                p = self._produto_by_id(pid)
                if not p:
                    continue
                label = f"{p['nome']}"
                if p.get("marca"):
                    label += f" ({p['marca']})"
                if p.get("tamanho"):
                    label += f" {p['tamanho']}{p.get('unidade','')}"
                label += f" | Estoque: {estoque_estimado if estoque_estimado is not None else p.get('quantidade',0)}"
                label += f" | {_money(p.get('preco_venda',0))}"
                self.cb_produto.setItemText(i, label)
                break

    def _on_cell_changed(self, row, column):
        if column not in (4, 6):
            return
        try:
            pid = int(self.tbl.item(row, 0).text())
            qtd = max(1, int(self.tbl.item(row, 4).text()))
            desconto = max(0.0, float(self.tbl.item(row, 6).text()))
            item = next(it for it in self.carrinho if it["produto_id"] == pid)
            item["quantidade"] = qtd
            item["desconto"] = desconto
            item["subtotal"] = qtd * float(item["preco_unitario"]) * (1 - desconto / 100)
            self.tbl.item(row, 7).setText(_money(item["subtotal"]))
            self.atualizar_totais()
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Erro ao atualizar item: {e}")

    # --- Totais e finalização ---
    def total(self) -> float:
        return sum(float(it["subtotal"]) for it in self.carrinho)

    def atualizar_totais(self):
        t = self.total()
        forma = self.cb_pag.currentText().upper()

        if forma == "CREDIARIO":
            self.lbl_total.setText(f"TOTAL: {_money(t)}")
            self.lbl_troco.setText("Pagamento lançado no crediário")
            return

        pago = float(self.sp_pago.value())
        troco = max(0.0, pago - t)

        self.lbl_total.setText(f"TOTAL: {_money(t)}")
        self.lbl_troco.setText(f"Troco: {_money(troco)}")

    def finalizar(self):
        if not self.carrinho:
            QMessageBox.warning(self, "Aviso", "Adicione itens na venda.")
            return

        cliente_id = self.cb_cliente.currentData()
        forma = self.cb_pag.currentText().strip().upper()
        if forma == "CREDIARIO" and not cliente_id:
            QMessageBox.warning(
                self,
                "Cliente obrigatório",
                "Para vendas no crediário selecione um cliente."
            )
            return
        pago = float(self.sp_pago.value())
        obs = self.ed_obs.toPlainText().strip()

        itens = [
            {"produto_id": int(it["produto_id"]),
            "quantidade": int(it["quantidade"]),
            "preco_unitario": float(it["preco_unitario"]),
            "desconto": float(it.get("desconto", 0))}
            for it in self.carrinho
        ]

        # Cria venda
        try:
            venda_id = criar_venda(
                usuario_id=self.usuario_id,
                cliente_id=cliente_id,
                forma_pagamento=forma,
                itens=itens,
                valor_pago=pago,
                observacoes=obs,
            )
        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))
            return

        # --- Gera PDF ---
        try:
            dados = obter_dados_venda(venda_id)
            pdf_path = gerar_recibo_80mm(dados)
        except Exception as e:
            QMessageBox.warning(self, "Aviso", f"Venda finalizada, mas erro ao gerar recibo: {e}")
            pdf_path = None

        QMessageBox.information(self, "Sucesso", f"Venda finalizada! ID: {venda_id}")

        self.carrinho.clear()
        self.ed_obs.clear()
        self.sp_pago.setValue(0)
        self.render_carrinho()
        self.atualizar_totais()
        self.carregar()

        # --- Abrir PDF ---
        if pdf_path and os.path.exists(pdf_path):
            if os.name == "nt":
                os.startfile(pdf_path)
            else:
                subprocess.Popen(["xdg-open", pdf_path])
