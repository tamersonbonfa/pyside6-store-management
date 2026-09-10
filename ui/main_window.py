from __future__ import annotations

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QStackedWidget
)

# Importamos as configurações globais
from config import NOME_LOJA, VERSAO_SISTEMA
from services.config_service import get_config, set_config
from services.auth_service import Usuario
from ui.themes import qss_light, qss_dark

from ui.tela_produtos import TelaProdutos
from ui.tela_clientes import TelaClientes
from ui.tela_vendas import TelaVendas
from ui.tela_usuarios import TelaUsuarios
from ui.tela_relatorios import TelaRelatorios


class MainWindow(QMainWindow):
    def __init__(self, usuario: Usuario):
        super().__init__()
        self.usuario = usuario
        self.usuario_id = usuario.id
        self.username = usuario.username
        self.nome = usuario.nome
        self.cargo = usuario.cargo
        self.is_admin = usuario.is_admin

        # 1. Configurações da Janela
        self.setWindowTitle(f"{NOME_LOJA} - v{VERSAO_SISTEMA}")
        self.resize(1200, 720)

        self.central = QWidget()
        self.setCentralWidget(self.central)

        root = QHBoxLayout(self.central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # --- SIDEBAR ---
        self.sidebar = QWidget()
        self.sidebar.setObjectName("Sidebar")
        sb = QVBoxLayout(self.sidebar)
        sb.setContentsMargins(14, 14, 14, 14)
        sb.setSpacing(10)

        logo = QLabel(NOME_LOJA)
        logo.setStyleSheet("font-size: 20px; font-weight: 900; margin-bottom: 5px;")
        sb.addWidget(logo)

        user_info = QLabel(
            f"👤 {self.nome}\n"
            f"💼 {self.cargo}"
        )
        user_info.setStyleSheet("opacity: 0.85; font-size: 12px; margin-bottom: 10px;")
        sb.addWidget(user_info)

        self.btn_vendas = QPushButton("🧾 Frente de Vendas")
        self.btn_produtos = QPushButton("📦 Produtos / Estoque")
        self.btn_clientes = QPushButton("👤 Clientes")
        
        sb.addWidget(self.btn_vendas)
        sb.addWidget(self.btn_produtos)
        sb.addWidget(self.btn_clientes)

        if self.is_admin:
            sb.addSpacing(10)
            line = QWidget()
            line.setFixedHeight(1)
            line.setStyleSheet("background-color: rgba(255,255,255,0.1);")
            sb.addWidget(line)
            sb.addSpacing(5)
            self.btn_relatorios = QPushButton("📊 Relatórios Gerenciais")
            self.btn_usuarios = QPushButton("🔑 Gestão de Usuários")
            sb.addWidget(self.btn_relatorios)
            sb.addWidget(self.btn_usuarios)

        self.btn_tema = QPushButton("🌙 Tema: Escuro")
        self.btn_tema.setObjectName("Primary")
        sb.addStretch(1)
        sb.addWidget(self.btn_tema)

        # --- ÁREA DE CONTEÚDO ---
        self.stack = QStackedWidget()
        
        # Inicializando as Telas
        self.tela_vendas = TelaVendas(usuario_id=self.usuario_id)
        self.tela_produtos = TelaProdutos(usuario_id=self.usuario_id)
        self.tela_clientes = TelaClientes()
        
        self.stack.addWidget(self.tela_vendas)   # Index 0
        self.stack.addWidget(self.tela_produtos) # Index 1
        self.stack.addWidget(self.tela_clientes) # Index 2

        if self.is_admin:
            self.tela_relatorios = TelaRelatorios()
            self.tela_usuarios = TelaUsuarios(usuario=self.usuario)
            self.stack.addWidget(self.tela_relatorios) # Index 3
            self.stack.addWidget(self.tela_usuarios)   # Index 4

        # ✅ CONEXÃO DO SINAL (Depois de criar as telas e o stack)
        self.stack.currentChanged.connect(self.atualizar_tela_ativa)

        root.addWidget(self.sidebar)
        root.addWidget(self.stack, 1)

        # --- EVENTOS ---
        self.btn_vendas.clicked.connect(lambda: self.stack.setCurrentWidget(self.tela_vendas))
        self.btn_produtos.clicked.connect(lambda: self.stack.setCurrentWidget(self.tela_produtos))
        self.btn_clientes.clicked.connect(lambda: self.stack.setCurrentWidget(self.tela_clientes))

        if self.is_admin:
            self.btn_relatorios.clicked.connect(lambda: self.stack.setCurrentWidget(self.tela_relatorios))
            self.btn_usuarios.clicked.connect(lambda: self.stack.setCurrentWidget(self.tela_usuarios))

        self.btn_tema.clicked.connect(self.toggle_theme)
        self.apply_theme(get_config("theme", "dark"))

    # ⚠️ A FUNÇÃO DEVE FICAR AQUI, FORA DO __INIT__
    def atualizar_tela_ativa(self):
        tela_atual = self.stack.currentWidget()
        
        # Tenta primeiro 'atualizar', se não existir, tenta 'carregar'
        if hasattr(tela_atual, "atualizar"):
            tela_atual.atualizar()
        elif hasattr(tela_atual, "carregar"):
            tela_atual.carregar()
        elif hasattr(tela_atual, "load_data"):
            tela_atual.load_data()

    def apply_theme(self, theme: str):
        theme = (theme or "dark").lower()
        if theme == "light":
            self.setStyleSheet(qss_light())
            self.btn_tema.setText("🌙 Tema: Escuro")
            set_config("theme", "light")
        else:
            self.setStyleSheet(qss_dark())
            self.btn_tema.setText("☀️ Tema: Claro")
            set_config("theme", "dark")

    def toggle_theme(self):
        current = get_config("theme", "dark").lower()
        new_theme = "light" if current == "dark" else "dark"
        self.apply_theme(new_theme)