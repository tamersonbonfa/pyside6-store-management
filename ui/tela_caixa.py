from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
)

from services.caixa_service import (
    saldo_caixa,
    listar_movimentacoes_caixa
)


def _money(valor):
    return (
        f"R$ {valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


class TelaCaixa(QWidget):

    def __init__(self, usuario_id: int):
        super().__init__()

        self.usuario_id = usuario_id

        layout = QVBoxLayout(self)


        titulo = QLabel("💰 Caixa")
        titulo.setStyleSheet(
            """
            font-size:20px;
            font-weight:bold;
            """
        )

        layout.addWidget(titulo)


        # Saldo atual

        self.lbl_saldo = QLabel(
            "Saldo: R$ 0,00"
        )

        self.lbl_saldo.setStyleSheet(
            """
            font-size:18px;
            padding:10px;
            """
        )

        layout.addWidget(
            self.lbl_saldo
        )


        # Botões

        barra = QHBoxLayout()


        self.btn_atualizar = QPushButton(
            "🔄 Atualizar"
        )

        self.btn_sangria = QPushButton(
            "➖ Sangria"
        )

        self.btn_entrada = QPushButton(
            "➕ Entrada Manual"
        )


        barra.addWidget(
            self.btn_atualizar
        )

        barra.addWidget(
            self.btn_sangria
        )

        barra.addWidget(
            self.btn_entrada
        )

        barra.addStretch()


        layout.addLayout(barra)


        # Tabela

        self.tabela = QTableWidget()

        self.tabela.setColumnCount(5)

        self.tabela.setHorizontalHeaderLabels(
            [
                "Data",
                "Tipo",
                "Descrição",
                "Valor",
                "Usuário"
            ]
        )


        self.tabela.setEditTriggers(
            QTableWidget.NoEditTriggers
        )


        layout.addWidget(
            self.tabela
        )


        self.btn_atualizar.clicked.connect(
            self.carregar
        )


        self.carregar()


    def carregar(self):

        try:

            saldo = saldo_caixa()

            self.lbl_saldo.setText(
                f"Saldo: {_money(saldo / 100)}"
            )


            movimentos = listar_movimentacoes_caixa()


            self.tabela.setRowCount(0)


            for mov in movimentos:

                linha = self.tabela.rowCount()

                self.tabela.insertRow(
                    linha
                )


                valor = mov["valor_centavos"]

                if mov["tipo"] in (
                    "SAIDA",
                    "SANGRIA"
                ):
                    valor = -valor


                dados = [
                    mov["data"],
                    mov["tipo"],
                    mov["descricao"],
                    _money(valor / 100),
                    mov.get("usuario_nome","")
                ]


                for coluna, item in enumerate(dados):

                    self.tabela.setItem(
                        linha,
                        coluna,
                        QTableWidgetItem(
                            str(item)
                        )
                    )


            self.tabela.resizeColumnsToContents()


        except Exception as e:

            QMessageBox.critical(
                self,
                "Erro",
                str(e)
            )