from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QFrame)
from PySide6.QtCore import Qt, QDate
from services.relatorios_service import RelatoriosService

class CardInfo(QFrame):
    def __init__(self, titulo, valor, cor="#2ecc71"):
        super().__init__()
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(f"background-color: rgba(255,255,255,0.05); border-radius: 8px; border-left: 5px solid {cor};")
        lay = QVBoxLayout(self)
        self.lbl_titulo = QLabel(titulo.upper())
        self.lbl_titulo.setStyleSheet("font-size: 10px; font-weight: bold; opacity: 0.7;")
        self.lbl_valor = QLabel(valor)
        self.lbl_valor.setStyleSheet("font-size: 18px; font-weight: 900;")
        lay.addWidget(self.lbl_titulo)
        lay.addWidget(self.lbl_valor)

    def atualizar(self, valor):
        self.lbl_valor.setText(valor)

class TelaRelatorios(QWidget):
    def __init__(self):
        super().__init__()
        self.service = RelatoriosService()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Barra Superior de Filtros
        filtros = QHBoxLayout()
        periodos = [("Hoje", "hoje"), ("Semana", "semana"), ("Mês", "mes"), ("Ano", "ano")]
        for texto, chave in periodos:
            btn = QPushButton(texto)
            btn.clicked.connect(lambda _, c=chave: self.carregar_dados(c))
            filtros.addWidget(btn)
        layout.addLayout(filtros)

        # Painel de Cards
        cards_layout = QHBoxLayout()
        self.card_fat = CardInfo("Faturamento", "R$ 0,00", "#2ecc71")
        self.card_vendas = CardInfo("Total Vendas", "0", "#3498db")
        self.card_ticket = CardInfo("Ticket Médio", "R$ 0,00", "#f1c40f")
        self.card_lucro = CardInfo("Lucro Est. (Bruto)", "R$ 0,00", "#e67e22")
        for c in [self.card_fat, self.card_vendas, self.card_ticket, self.card_lucro]:
            cards_layout.addWidget(c)
        layout.addLayout(cards_layout)

        # Seção Central
        corpo = QHBoxLayout()
        
        # Tabela 1: Detalhamento de Produtos (9 Colunas)
        v_prod = QVBoxLayout()
        v_prod.addWidget(QLabel("<b>📦 DETALHAMENTO POR PRODUTO (PERÍODO)</b>"))
        self.tab_produtos = QTableWidget(0, 9) 
        self.tab_produtos.setHorizontalHeaderLabels([
            "Produto", "Qtd", "Tam.", "Un.", "Preço Compra", "Preço Venda", "Descontos (R$)", "Total Faturado", "Lucro Est."
        ])
        
        # Bloqueia edição das células
        self.tab_produtos.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        
        header = self.tab_produtos.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, 9):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        
        v_prod.addWidget(self.tab_produtos)
        
        # Tabela 2: Info Lateral
        v_info = QVBoxLayout()
        v_info.addWidget(QLabel("<b>💳 MEIOS DE PAGAMENTO</b>"))
        self.tab_pagos = QTableWidget(0, 2)
        self.tab_pagos.setHorizontalHeaderLabels(["Forma", "Total"])
        # Bloqueia edição das células
        self.tab_pagos.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.tab_pagos.setFixedHeight(150)
        v_info.addWidget(self.tab_pagos)

        v_info.addWidget(QLabel("<b>⚠️ ESTOQUE CRÍTICO</b>"))
        self.tab_estoque = QTableWidget(0, 2)
        self.tab_estoque.setHorizontalHeaderLabels(["Item", "Atual"])
        # Bloqueia edição das células
        self.tab_estoque.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        v_info.addWidget(self.tab_estoque)

        corpo.addLayout(v_prod, 3) 
        corpo.addLayout(v_info, 1)
        layout.addLayout(corpo)

        self.carregar_dados("mes")

    def carregar_dados(self, periodo):
        hoje = QDate.currentDate()
        # O fim deve ser sempre hoje para os filtros rápidos
        fim_str = hoje.toString("yyyy-MM-dd")
        
        # Define o início baseado no botão clicado
        if periodo == "hoje":
            inicio_str = hoje.toString("yyyy-MM-dd")
        elif periodo == "semana":
            # Pega os últimos 7 dias
            inicio_str = hoje.addDays(-7).toString("yyyy-MM-dd")
        elif periodo == "mes":
            # Primeiro dia do mês atual
            inicio_str = hoje.toString("yyyy-MM-01")
        elif periodo == "ano":
            # Primeiro dia do ano atual
            inicio_str = hoje.toString("yyyy-01-01")
        else:
            inicio_str = hoje.toString("yyyy-MM-01")

        # Chama o service passando o intervalo corrigido
        # É vital que o service adicione " 00:00:00" e " 23:59:59" no SQL
        dados = self.service.resumo_detalhado(inicio_str, fim_str)
        self.atualizar_interface(dados)

    def atualizar_interface(self, dados):
        fin = dados["financeiro"]
        if fin:
            self.card_fat.atualizar(f"R$ {fin['faturamento']:,.2f}")
            self.card_vendas.atualizar(str(fin['total_vendas']))
            self.card_ticket.atualizar(f"R$ {fin['ticket_medio']:,.2f}")
            lucro_total = sum(p['lucro_estimado'] for p in dados['produtos'])
            self.card_lucro.atualizar(f"R$ {lucro_total:,.2f}")
        
        self.tab_produtos.setRowCount(0)
        for i, p in enumerate(dados["produtos"]):
            self.tab_produtos.insertRow(i)
            self.tab_produtos.setItem(i, 0, QTableWidgetItem(p['nome']))
            self.tab_produtos.setItem(i, 1, QTableWidgetItem(str(p['qtd_vendida']))) # QUANTIDADE ADICIONADA AQUI
            self.tab_produtos.setItem(i, 2, QTableWidgetItem(str(p['tamanho'])))
            self.tab_produtos.setItem(i, 3, QTableWidgetItem(p['unidade']))
            self.tab_produtos.setItem(i, 4, QTableWidgetItem(f"R$ {p['preco_compra']:,.2f}"))
            self.tab_produtos.setItem(i, 5, QTableWidgetItem(f"R$ {p['preco_venda']:,.2f}"))
            
            item_desc = QTableWidgetItem(f"R$ {p['desconto_total_reais']:,.2f}")
            if p['desconto_total_reais'] > 0: item_desc.setForeground(Qt.red)
            self.tab_produtos.setItem(i, 6, item_desc)
            
            self.tab_produtos.setItem(i, 7, QTableWidgetItem(f"R$ {p['total_faturado']:,.2f}"))
            
            item_lucro = QTableWidgetItem(f"R$ {p['lucro_estimado']:,.2f}")
            item_lucro.setForeground(Qt.green if p['lucro_estimado'] > 0 else Qt.red)
            self.tab_produtos.setItem(i, 8, item_lucro)

        # Tabela Pagos e Estoque
        self.tab_pagos.setRowCount(0)
        for i, pag in enumerate(dados["pagamentos"]):
            self.tab_pagos.insertRow(i)
            self.tab_pagos.setItem(i, 0, QTableWidgetItem(pag['forma_pagamento']))
            self.tab_pagos.setItem(i, 1, QTableWidgetItem(f"R$ {pag['total']:,.2f}"))

        self.tab_estoque.setRowCount(0)
        for i, est in enumerate(dados["estoque_baixo"]):
            self.tab_estoque.insertRow(i)
            item = QTableWidgetItem(est['nome'])
            if est['quantidade'] <= 0: item.setForeground(Qt.red)
            self.tab_estoque.setItem(i, 0, item)
            self.tab_estoque.setItem(i, 1, QTableWidgetItem(str(est['quantidade'])))
        
    def atualizar(self):
    # Chama a função que você já tem, usando 'mes' como padrão
        self.carregar_dados("mes")