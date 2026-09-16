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

from services.crediario_service import listar_clientes_devedores


def _money(valor: float) -> str:
    return (
        f"R$ {valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


class TelaRelatorioCrediario(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        titulo = QLabel("📊 Relatório de Crediário")
        titulo.setStyleSheet(
            "font-size: 20px; font-weight: bold;"
        )

        layout.addWidget(titulo)


        barra = QHBoxLayout()

        self.btn_atualizar = QPushButton(
            "🔄 Atualizar"
        )

        barra.addWidget(
            self.btn_atualizar
        )

        barra.addStretch()

        layout.addLayout(barra)


        self.tabela = QTableWidget()

        self.tabela.setColumnCount(6)

        self.tabela.setHorizontalHeaderLabels([
            "Cliente",
            "Telefone",
            "Contas",
            "Total Comprado",
            "Total Pago",
            "Saldo Devedor",
        ])

        self.tabela.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
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

            dados = listar_clientes_devedores()

            self.tabela.setRowCount(0)


            for cliente in dados:

                linha = self.tabela.rowCount()

                self.tabela.insertRow(
                    linha
                )


                valores = [
                    cliente["nome"],
                    cliente.get("telefone") or "",
                    cliente["quantidade_contas"],
                    _money(cliente["total_devido"]),
                    _money(cliente["total_pago"]),
                    _money(cliente["saldo_devedor"]),
                ]


                for coluna, valor in enumerate(valores):

                    self.tabela.setItem(
                        linha,
                        coluna,
                        QTableWidgetItem(str(valor))
                    )


            self.tabela.resizeColumnsToContents()


        except Exception as e:

            QMessageBox.critical(
                self,
                "Erro",
                str(e)
            )
