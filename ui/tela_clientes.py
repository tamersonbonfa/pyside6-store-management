from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QFormLayout, QDialog,
    QTextEdit, QCheckBox
)

from services.clientes_service import (
    listar_clientes,
    buscar_clientes,
    criar_cliente,
    atualizar_cliente,
)


class ClienteDialog(QDialog):
    def __init__(self, parent=None, cliente: dict | None = None):
        super().__init__(parent)
        self.setWindowTitle("Cliente")
        self.setMinimumWidth(560)

        self.cliente = cliente

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(10)

        self.ed_nome = QLineEdit()
        self.ed_tel = QLineEdit()
        self.ed_end = QLineEdit()
        self.chk_ativo = QCheckBox("Cliente ativo")
        self.chk_ativo.setChecked(True)

        self.ed_obs = QTextEdit()
        self.ed_obs.setFixedHeight(120)

        form.addRow("Nome*", self.ed_nome)
        form.addRow("", self.chk_ativo)
        form.addRow("Telefone", self.ed_tel)
        form.addRow("Endereço", self.ed_end)
        form.addRow("Observações", self.ed_obs)

        layout.addLayout(form)

        row = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_ok = QPushButton("Salvar")
        btn_ok.setObjectName("Primary")

        btn_cancel.clicked.connect(self.reject)
        btn_ok.clicked.connect(self.accept)

        row.addWidget(btn_cancel)
        row.addWidget(btn_ok)
        layout.addLayout(row)

        if cliente:
            self._fill(cliente)

    def _fill(self, c: dict):
        self.ed_nome.setText(str(c.get("nome") or ""))
        self.chk_ativo.setChecked(bool(c.get("ativo")))
        self.ed_tel.setText(str(c.get("telefone") or ""))
        self.ed_end.setText(str(c.get("endereco") or ""))
        self.ed_obs.setPlainText(str(c.get("observacoes") or ""))

    def get_data(self) -> dict:
        return {
            "nome": self.ed_nome.text().strip(),
            "ativo": self.chk_ativo.isChecked(),
            "telefone": self.ed_tel.text().strip(),
            "endereco": self.ed_end.text().strip(),
            "observacoes": self.ed_obs.toPlainText().strip(),
        }


class TelaClientes(QWidget):
    def __init__(self):
        super().__init__()
        self.clientes_cache: list[dict] = []

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel("👤 Clientes")
        title.setObjectName("Title")

        self.ed_busca = QLineEdit()
        self.ed_busca.setPlaceholderText("Buscar por nome ou telefone...")

        self.btn_novo = QPushButton("➕ Novo Cliente")
        self.btn_novo.setObjectName("Primary")

        self.btn_refresh = QPushButton("🔄 Atualizar")

        header.addWidget(title, 1)
        header.addWidget(self.ed_busca, 1)
        header.addWidget(self.btn_refresh)
        header.addWidget(self.btn_novo)

        layout.addLayout(header)

        self.tbl = QTableWidget(0, 6)
        self.tbl.setHorizontalHeaderLabels(["ID", "Nome", "Status", "Telefone", "Endereço", "Criado em"])
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl.setAlternatingRowColors(True)

        layout.addWidget(self.tbl, 1)

        actions = QHBoxLayout()
        self.btn_editar = QPushButton("✏️ Editar")
        actions.addWidget(self.btn_editar)
        actions.addStretch(1)

        layout.addLayout(actions)

        # Eventos
        self.btn_novo.clicked.connect(self.novo_cliente)
        self.btn_refresh.clicked.connect(self.carregar)
        self.ed_busca.textChanged.connect(self.buscar)
        self.btn_editar.clicked.connect(self.editar)
        self.tbl.doubleClicked.connect(self.editar)

        self.carregar()

    def _selected_cliente(self) -> dict | None:
        row = self.tbl.currentRow()
        if row < 0:
            return None
        cid = int(self.tbl.item(row, 0).text())
        for c in self.clientes_cache:
            if int(c["id"]) == cid:
                return c
        return None

    def carregar(self):
        self.clientes_cache = listar_clientes()
        self._render(self.clientes_cache)

    def buscar(self):
        texto = self.ed_busca.text().strip()
        self.clientes_cache = buscar_clientes(texto)
        self._render(self.clientes_cache)

    def _render(self, data: list[dict]):
        self.tbl.setRowCount(0)

        for c in data:
            r = self.tbl.rowCount()
            self.tbl.insertRow(r)

            values = [
                str(c["id"]),
                str(c.get("nome") or ""),
                "Ativo" if c.get("ativo") else "Inativo",
                str(c.get("telefone") or ""),
                str(c.get("endereco") or ""),
                str(c.get("criado_em") or ""),
            ]

            for col, v in enumerate(values):
                it = QTableWidgetItem(v)
                if col == 0:
                    it.setTextAlignment(Qt.AlignCenter)
                self.tbl.setItem(r, col, it)

        self.tbl.resizeColumnsToContents()

    def novo_cliente(self):
        dlg = ClienteDialog(self, cliente=None)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        d = dlg.get_data()
        try:
            criar_cliente(
                nome=d["nome"],
                telefone=d["telefone"],
                endereco=d["endereco"],
                observacoes=d["observacoes"],
            )
            self.carregar()
        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))

    def editar(self):
        c = self._selected_cliente()
        if not c:
            QMessageBox.information(self, "Aviso", "Selecione um cliente.")
            return

        dlg = ClienteDialog(self, cliente=c)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        d = dlg.get_data()
        try:
            atualizar_cliente(
                cliente_id=int(c["id"]),
                nome=d["nome"],
                ativo=d["ativo"],
                telefone=d["telefone"],
                endereco=d["endereco"],
                observacoes=d["observacoes"],
            )
            self.carregar()
        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))
