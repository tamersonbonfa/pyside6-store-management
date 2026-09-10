from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QHBoxLayout, QMessageBox
)

# Importamos as variáveis de personalização do seu novo arquivo de configuração
from config import NOME_LOJA, SLOGAN_LOJA
from services.auth_service import authenticate, Usuario
from ui.main_window import MainWindow


class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        # 1. Título da Janela dinâmico
        self.setWindowTitle(f"{NOME_LOJA} - Login")
        self.setFixedSize(420, 260)

        self.user: Usuario | None = None
        self.main_window: MainWindow | None = None 

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # 2. Título visual dinâmico
        title = QLabel(NOME_LOJA)
        title.setObjectName("Title")

        # 3. Subtítulo usando o slogan ou texto de instrução
        subtitle = QLabel(SLOGAN_LOJA if SLOGAN_LOJA else "Entre com seu usuário e senha")
        subtitle.setStyleSheet("opacity: 0.8;")

        self.ed_user = QLineEdit()
        self.ed_user.setPlaceholderText("Usuário (ex: admin)")

        self.ed_pass = QLineEdit()
        self.ed_pass.setPlaceholderText("Senha")
        self.ed_pass.setEchoMode(QLineEdit.Password)

        btn_login = QPushButton("Entrar")
        btn_login.setObjectName("Primary")
        btn_login.clicked.connect(self._do_login)

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)

        row = QHBoxLayout()
        row.addWidget(btn_cancel)
        row.addWidget(btn_login)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(4)
        layout.addWidget(self.ed_user)
        layout.addWidget(self.ed_pass)
        layout.addSpacing(6)
        layout.addLayout(row)

        self.ed_pass.returnPressed.connect(self._do_login)

    def _do_login(self):
        u = self.ed_user.text().strip()
        p = self.ed_pass.text()

        user = authenticate(u, p)
        if not user:
            QMessageBox.warning(self, "Erro", "Usuário ou senha inválidos.")
            return

        self.user = user

        # ✅ ABRE A JANELA PRINCIPAL
        self.main_window = MainWindow(usuario=user)
        self.main_window.show()

        self.accept()