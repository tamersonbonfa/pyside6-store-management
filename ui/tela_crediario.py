from __future__ import annotations
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QAbstractItemView,
)

from services.crediario_service import listar_contas_receber, listar_pagamentos_conta
from ui.registrar_pagamento_dialog import RegistrarPagamentoDialog
from services.crediario_service import registrar_pagamento

def _money(valor: float) -> str:
    return (
        f"R$ {valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


class TelaCrediario(QWidget):

    def __init__(self, usuario_id: int):
        super().__init__()

        self.usuario_id = usuario_id
        self.conta_selecionada = None

        layout = QVBoxLayout(self)

        titulo = QLabel("💰 Crediário")
        titulo.setStyleSheet(
            "font-size: 20px; font-weight: bold;"
        )

        layout.addWidget(titulo)


        # Botões
        barra = QHBoxLayout()

        self.btn_atualizar = QPushButton(
            "🔄 Atualizar"
        )
        
        self.btn_pagar = QPushButton(
            "💰 Registrar Pagamento"
        )

        barra.addWidget(
            self.btn_atualizar
        )

        barra.addWidget(
            self.btn_pagar
        )

        barra.addStretch()

        layout.addLayout(barra)


        # Tabela

        self.tabela = QTableWidget()

        self.tabela.setColumnCount(7)

        self.tabela.setHorizontalHeaderLabels([
            "ID",
            "Cliente",
            "Venda",
            "Total",
            "Pago",
            "Saldo",
            "Status"
        ])

        # Bloqueia edição das células
        self.tabela.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        self.tabela.setSelectionBehavior(
            self.tabela.SelectionBehavior.SelectRows
        )

        self.tabela.setSelectionMode(
            self.tabela.SelectionMode.SingleSelection
        )
        layout.addWidget(
            self.tabela
        )

        # Painel de detalhes da conta selecionada
        self.lbl_detalhes = QLabel(
            "Nenhuma conta selecionada."
        )

        self.lbl_detalhes.setStyleSheet(
            """
            font-size: 14px;
            padding: 10px;
            border: 1px solid #555;
            """
        )

        self.lbl_detalhes.setWordWrap(True)

        layout.addWidget(self.lbl_detalhes)
        
        self.tabela_pagamentos = QTableWidget()

        self.tabela_pagamentos.setColumnCount(4)

        self.tabela_pagamentos.setHorizontalHeaderLabels([
            "Data/Hora",
            "Valor",
            "Usuário",
            "Observação"
        ])

        self.tabela_pagamentos.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        layout.addWidget(
            QLabel("Histórico de pagamentos")
        )

        layout.addWidget(
            self.tabela_pagamentos
        )


        self.btn_atualizar.clicked.connect(
            self.carregar
        )
        
        self.btn_pagar.clicked.connect(
            self.registrar_pagamento
        )


        self.tabela.cellClicked.connect(
            self.selecionar_conta
        )


        self.carregar()


    def carregar(self):

        try:
            contas = listar_contas_receber()

            self.tabela.setRowCount(0)
            self.conta_selecionada = None

            for conta in contas:

                linha = self.tabela.rowCount()

                self.tabela.insertRow(linha)

                valores = [
                    conta["id"],
                    conta["cliente_nome"],
                    conta["venda_id"],
                    _money(conta["valor_centavos"] / 100),
                    _money(conta["valor_pago_centavos"] / 100),
                    _money(conta["saldo_centavos"] / 100),
                    conta["status"],
                ]

                for coluna, valor in enumerate(valores):

                    item = QTableWidgetItem(str(valor))

                    self.tabela.setItem(
                        linha,
                        coluna,
                        item
                    )

                # TEM QUE FICAR AQUI DENTRO DO FOR
                self.tabela.item(linha, 0).setData(
                    Qt.ItemDataRole.UserRole,
                    conta
                )

            self.tabela.resizeColumnsToContents()


        except Exception as e:

            QMessageBox.critical(
                self,
                "Erro",
                str(e)
            )
            
    def selecionar_conta(self):

        itens = self.tabela.selectedItems()

        if not itens:
            self.conta_selecionada = None
            self.lbl_detalhes.setText(
                "Nenhuma conta selecionada."
            )
            return


        linha = itens[0].row()

        item = self.tabela.item(linha, 0)

        if not item:
            return


        conta = item.data(
            Qt.ItemDataRole.UserRole
        )


        if conta:
            self.conta_selecionada = conta

            self.carregar_pagamentos(
                conta["id"]
            )


            saldo = conta["saldo_centavos"] / 100
            pago = conta["valor_pago_centavos"] / 100
            valor = conta["valor_centavos"] / 100


            self.lbl_detalhes.setText(
                f"""
    <b>Cliente:</b> {conta['cliente_nome']}<br>
    <b>Venda:</b> #{conta['venda_id']}<br>
    <br>
    <b>Valor da compra:</b> R$ {valor:.2f}<br>
    <b>Pago:</b> R$ {pago:.2f}<br>
    <b>Saldo devedor:</b> R$ {saldo:.2f}<br>
    <br>
    <b>Status:</b> {conta['status']}<br>
    <b>Criado em:</b> {conta['data_criacao']}
    """
            )

    
    def registrar_pagamento(self):

        if not self.conta_selecionada:
            QMessageBox.warning(
                self,
                "Aviso",
                "Selecione uma conta."
            )
            return


        saldo = self.conta_selecionada["saldo_centavos"] / 100

        dialog = RegistrarPagamentoDialog(
            saldo,
            self
        )


        if dialog.exec():

            valor_centavos = int(
                round(
                    dialog.valor * 100
                )
            )


            try:

                registrar_pagamento(
                    conta_id=self.conta_selecionada["id"],
                    valor_pago=valor_centavos,
                    usuario_id=self.usuario_id,
                    observacao=dialog.observacao
                )


                QMessageBox.information(
                    self,
                    "Sucesso",
                    "Pagamento registrado."
                )

                self.carregar()


            except Exception as e:

                QMessageBox.critical(
                    self,
                    "Erro",
                    str(e)
                )
                
    def carregar_pagamentos(self, conta_id: int):

        pagamentos = listar_pagamentos_conta(conta_id)

        self.tabela_pagamentos.setRowCount(0)

        for pagamento in pagamentos:

            linha = self.tabela_pagamentos.rowCount()

            self.tabela_pagamentos.insertRow(linha)

            valores = [
                pagamento["data"],
                _money(pagamento["valor"]),
                pagamento.get("usuario_nome") or "Desconhecido",
                pagamento.get("observacao") or "",
            ]

            for coluna, valor in enumerate(valores):

                self.tabela_pagamentos.setItem(
                    linha,
                    coluna,
                    QTableWidgetItem(str(valor))
                )

        self.tabela_pagamentos.resizeColumnsToContents()