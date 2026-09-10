# ui/tela_usuarios.py
from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QDialog, QFormLayout,
    QMessageBox, QCheckBox
)
from services.usuario_service import listar_usuarios, criar_usuario, atualizar_usuario


class TelaUsuarios(QWidget):
    def __init__(self, usuario):
        super().__init__()
        
        self.usuario = usuario
        
        self.setObjectName("TelaUsuarios")

        self.layout = QVBoxLayout(self)

        # Cabeçalho
        header_layout = QHBoxLayout()
        self.layout.addLayout(header_layout)

        self.label_title = QLabel("Usuários")
        self.label_title.setStyleSheet("font-weight: 700; font-size: 18px;")
        header_layout.addWidget(self.label_title)

        header_layout.addStretch(1)

        self.btn_adicionar = QPushButton("➕ Adicionar")
        header_layout.addWidget(self.btn_adicionar)
        self.btn_adicionar.clicked.connect(self.adicionar_usuario)

        # Tabela de usuários
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(6)
        self.tabela.setHorizontalHeaderLabels(["ID", "Usuário", "Nome", "Cargo","Admin", "Ativo"])
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela.cellDoubleClicked.connect(self.editar_usuario)
        self.layout.addWidget(self.tabela)

        self.carregar_usuarios()

    def carregar_usuarios(self):
        self.tabela.setRowCount(0)
        usuarios = listar_usuarios()
        for usuario in usuarios:
            row = self.tabela.rowCount()
            self.tabela.insertRow(row)
            self.tabela.setItem(row, 0, QTableWidgetItem(str(usuario["id"])))
            self.tabela.setItem(row, 1, QTableWidgetItem(usuario["username"]))
            self.tabela.setItem(row, 2, QTableWidgetItem(usuario["nome"]))
            self.tabela.setItem(row, 3, QTableWidgetItem(usuario["cargo"]))
            self.tabela.setItem(row, 4, QTableWidgetItem("Sim" if usuario["is_admin"] else "Não"))
            self.tabela.setItem(row, 5, QTableWidgetItem("Sim" if usuario["ativo"] else "Não"))

    def adicionar_usuario(self):
        dialog = DialogUsuario()
        if dialog.exec():
            data = dialog.get_data()
            criar_usuario(**data)
            self.carregar_usuarios()

    def editar_usuario(self, row, column):
        usuario_id = int(self.tabela.item(row, 0).text())
        dialog = DialogUsuario(usuario_id=usuario_id)
        if dialog.exec():
            data = dialog.get_data()
            atualizar_usuario(usuario_id, **data)
            self.carregar_usuarios()


class DialogUsuario(QDialog):
    def __init__(self, usuario_id: int | None = None):
        super().__init__()
        self.usuario_id = usuario_id
        self.setWindowTitle("Cadastro de Usuário" if not usuario_id else "Editar Usuário")
        self.setMinimumWidth(300)

        self.layout = QVBoxLayout(self)

        form = QFormLayout()
        self.layout.addLayout(form)

        self.input_username = QLineEdit()
        self.input_nome = QLineEdit()
        self.input_cargo = QLineEdit()
        self.input_senha = QLineEdit()
        self.input_senha.setEchoMode(QLineEdit.Password)
        self.checkbox_admin = QCheckBox("Administrador")
        self.checkbox_ativo = QCheckBox("Ativo")

        form.addRow("Usuário:", self.input_username)
        form.addRow("Nome:", self.input_nome)
        form.addRow("Cargo:", self.input_cargo)
        form.addRow("Senha:", self.input_senha)
        form.addRow("", self.checkbox_admin)
        form.addRow("", self.checkbox_ativo)

        # Botões
        btn_layout = QHBoxLayout()
        self.layout.addLayout(btn_layout)
        self.btn_salvar = QPushButton("Salvar")
        self.btn_cancelar = QPushButton("Cancelar")
        btn_layout.addStretch(1)
        btn_layout.addWidget(self.btn_salvar)
        btn_layout.addWidget(self.btn_cancelar)

        self.btn_cancelar.clicked.connect(self.reject)
        self.btn_salvar.clicked.connect(self.salvar)

        # Se for edição, carregar dados
        if usuario_id:
            from services.usuario_service import buscar_usuario_por_id
            usuario = buscar_usuario_por_id(usuario_id)
            if usuario:
                self.input_username.setText(usuario["username"])
                self.input_nome.setText(usuario["nome"])
                self.input_cargo.setText(usuario["cargo"])
                self.checkbox_admin.setChecked(usuario["is_admin"])
                self.checkbox_ativo.setChecked(usuario["ativo"])

    def salvar(self):
        username = self.input_username.text().strip()
        nome = self.input_nome.text().strip()
        cargo = self.input_cargo.text().strip()
        senha = self.input_senha.text().strip()
        is_admin = self.checkbox_admin.isChecked()
        ativo = self.checkbox_ativo.isChecked()

        if not username or not nome or not cargo or (not self.usuario_id and not senha):
            QMessageBox.warning(self, "Erro", "Preencha todos os campos obrigatórios.")
            return

        self._data = {
            "username": username,
            "nome": nome,
            "cargo": cargo,
            "senha": senha or None,  # se editar e deixar em branco, senha não muda
            "is_admin": is_admin,
            "ativo": ativo
        }
        self.accept()

    def get_data(self) -> dict:
        return self._data
