from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QFormLayout
)

from services.usuario_service import criar_usuario


class AdminSetupDialog(QDialog):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Configuração inicial")
        self.setMinimumWidth(350)

        layout = QVBoxLayout(self)

        titulo = QLabel("Criar administrador inicial")
        titulo.setStyleSheet(
            "font-size: 18px; font-weight: bold;"
        )

        layout.addWidget(titulo)

        form = QFormLayout()

        self.input_username = QLineEdit()
        self.input_nome = QLineEdit()
        self.input_cargo = QLineEdit()
        self.input_senha = QLineEdit()

        self.input_senha.setEchoMode(
            QLineEdit.Password
        )

        self.input_cargo.setText("Administrador")

        form.addRow("Usuário:", self.input_username)
        form.addRow("Nome:", self.input_nome)
        form.addRow("Cargo:", self.input_cargo)
        form.addRow("Senha:", self.input_senha)

        layout.addLayout(form)

        self.btn_criar = QPushButton(
            "Criar administrador"
        )

        layout.addWidget(self.btn_criar)

        self.btn_criar.clicked.connect(
            self.criar_admin
        )


    def criar_admin(self):

        username = self.input_username.text().strip()
        nome = self.input_nome.text().strip()
        cargo = self.input_cargo.text().strip()
        senha = self.input_senha.text().strip()

        if not username or not nome or not cargo or not senha:
            QMessageBox.warning(
                self,
                "Erro",
                "Preencha todos os campos."
            )
            return

        try:
            criar_usuario(
                username=username,
                nome=nome,
                cargo=cargo,
                senha=senha,
                is_admin=True,
                ativo=True
            )

            QMessageBox.information(
                self,
                "Sucesso",
                "Administrador criado com sucesso."
            )

            self.accept()

        except Exception as erro:
            QMessageBox.critical(
                self,
                "Erro",
                str(erro)
            )