from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QDateEdit,
    QTableWidget,
    QTableWidgetItem,
    QGroupBox,
    QFormLayout,
    QMessageBox,
    QHeaderView,
    QDialog,
)
from PySide6.QtCore import QDate

from services.caixa_service import (
    resumo_relatorio_caixa,
    listar_movimentacoes_periodo,
    listar_caixas_periodo,
)


def _money_centavos(valor: int | None) -> str:
    valor = int(valor or 0)

    sinal = "-" if valor < 0 else ""

    valor = abs(valor)

    reais = valor // 100
    centavos = valor % 100

    texto = f"{reais:,}".replace(",", ".")

    return f"{sinal}R$ {texto},{centavos:02d}"


class TelaRelatorioCaixa(QDialog):
    
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Relatório do Caixa")

        layout = QVBoxLayout(self)

        # =========================================================
        # TÍTULO
        # =========================================================

        titulo = QLabel("📊 Relatório do Caixa")

        titulo.setStyleSheet(
            """
            font-size: 22px;
            font-weight: bold;
            padding: 10px;
            """
        )

        layout.addWidget(titulo)

        # =========================================================
        # FILTROS
        # =========================================================

        grupo_filtros = QGroupBox("Período")

        filtros = QHBoxLayout()

        self.data_inicio = QDateEdit()

        self.data_inicio.setCalendarPopup(True)

        self.data_inicio.setDate(
            QDate.currentDate()
        )

        self.data_fim = QDateEdit()

        self.data_fim.setCalendarPopup(True)

        self.data_fim.setDate(
            QDate.currentDate()
        )

        self.btn_atualizar = QPushButton(
            "🔄 Atualizar"
        )

        filtros.addWidget(
            QLabel("Data inicial:")
        )

        filtros.addWidget(
            self.data_inicio
        )

        filtros.addWidget(
            QLabel("Data final:")
        )

        filtros.addWidget(
            self.data_fim
        )

        filtros.addWidget(
            self.btn_atualizar
        )

        filtros.addStretch()

        grupo_filtros.setLayout(filtros)

        layout.addWidget(
            grupo_filtros
        )

        # =========================================================
        # RESUMO
        # =========================================================

        grupo_resumo = QGroupBox(
            "Resumo financeiro"
        )

        resumo_layout = QFormLayout()

        self.lbl_abertura = QLabel(
            "R$ 0,00"
        )

        self.lbl_vendas = QLabel(
            "R$ 0,00"
        )

        self.lbl_crediario = QLabel(
            "R$ 0,00"
        )

        self.lbl_entradas = QLabel(
            "R$ 0,00"
        )

        self.lbl_sangrias = QLabel(
            "R$ 0,00"
        )

        self.lbl_total_entradas = QLabel(
            "R$ 0,00"
        )

        self.lbl_total_saidas = QLabel(
            "R$ 0,00"
        )

        self.lbl_movimentacao_liquida = QLabel(
            "R$ 0,00"
        )

        resumo_layout.addRow(
            "Aberturas:",
            self.lbl_abertura
        )

        resumo_layout.addRow(
            "Vendas:",
            self.lbl_vendas
        )

        resumo_layout.addRow(
            "Recebimentos de crediário:",
            self.lbl_crediario
        )

        resumo_layout.addRow(
            "Entradas manuais:",
            self.lbl_entradas
        )

        resumo_layout.addRow(
            "Sangrias:",
            self.lbl_sangrias
        )

        resumo_layout.addRow(
            "Total de entradas:",
            self.lbl_total_entradas
        )

        resumo_layout.addRow(
            "Total de saídas:",
            self.lbl_total_saidas
        )

        resumo_layout.addRow(
            "Movimentação líquida:",
            self.lbl_movimentacao_liquida
        )

        grupo_resumo.setLayout(
            resumo_layout
        )

        layout.addWidget(
            grupo_resumo
        )

        # =========================================================
        # TABELA DE MOVIMENTAÇÕES
        # =========================================================

        titulo_movimentos = QLabel(
            "Movimentações"
        )

        titulo_movimentos.setStyleSheet(
            """
            font-size: 16px;
            font-weight: bold;
            padding-top: 10px;
            """
        )

        layout.addWidget(
            titulo_movimentos
        )

        self.tabela_movimentos = QTableWidget()

        self.tabela_movimentos.setColumnCount(7)

        self.tabela_movimentos.setHorizontalHeaderLabels(
            [
                "Data",
                "Tipo",
                "Descrição",
                "Forma de pagamento",
                "Valor",
                "Usuário",
                "Observação",
            ]
        )

        self.tabela_movimentos.setEditTriggers(
            QTableWidget.NoEditTriggers
        )

        self.tabela_movimentos.setSelectionBehavior(
            QTableWidget.SelectRows
        )

        self.tabela_movimentos.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )

        self.tabela_movimentos.horizontalHeader().setStretchLastSection(
            True
        )

        layout.addWidget(
            self.tabela_movimentos
        )

        # =========================================================
        # TABELA DE CAIXAS
        # =========================================================

        titulo_caixas = QLabel(
            "Histórico dos caixas"
        )

        titulo_caixas.setStyleSheet(
            """
            font-size: 16px;
            font-weight: bold;
            padding-top: 10px;
            """
        )

        layout.addWidget(
            titulo_caixas
        )

        self.tabela_caixas = QTableWidget()

        self.tabela_caixas.setColumnCount(9)

        self.tabela_caixas.setHorizontalHeaderLabels(
            [
                "Caixa",
                "Abertura",
                "Usuário abertura",
                "Valor inicial",
                "Status",
                "Fechamento",
                "Usuário fechamento",
                "Valor final",
                "Diferença",
            ]
        )

        self.tabela_caixas.setEditTriggers(
            QTableWidget.NoEditTriggers
        )

        self.tabela_caixas.setSelectionBehavior(
            QTableWidget.SelectRows
        )

        self.tabela_caixas.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )

        self.tabela_caixas.horizontalHeader().setStretchLastSection(
            True
        )

        layout.addWidget(
            self.tabela_caixas
        )

        # =========================================================
        # EVENTOS
        # =========================================================

        self.btn_atualizar.clicked.connect(
            self.carregar
        )

        # =========================================================
        # CARREGAMENTO INICIAL
        # =========================================================

        self.carregar()

    # =============================================================
    # CARREGAR RELATÓRIO
    # =============================================================

    def carregar(self):

        try:

            inicio = self.data_inicio.date().toString(
                "yyyy-MM-dd"
            )

            fim = self.data_fim.date().toString(
                "yyyy-MM-dd"
            )

            if inicio > fim:

                QMessageBox.warning(
                    self,
                    "Período inválido",
                    "A data inicial não pode ser maior que a data final."
                )

                return

            # =====================================================
            # RESUMO
            # =====================================================

            resumo = resumo_relatorio_caixa(
                inicio,
                fim
            )

            self.lbl_abertura.setText(
                _money_centavos(
                    resumo["abertura"]
                )
            )

            self.lbl_vendas.setText(
                _money_centavos(
                    resumo["vendas"]
                )
            )

            self.lbl_crediario.setText(
                _money_centavos(
                    resumo["recebimentos_crediario"]
                )
            )

            self.lbl_entradas.setText(
                _money_centavos(
                    resumo["entradas"]
                )
            )

            self.lbl_sangrias.setText(
                _money_centavos(
                    resumo["sangrias"]
                )
            )

            self.lbl_total_entradas.setText(
                _money_centavos(
                    resumo["total_entradas"]
                )
            )

            self.lbl_total_saidas.setText(
                _money_centavos(
                    resumo["total_saidas"]
                )
            )

            self.lbl_movimentacao_liquida.setText(
                _money_centavos(
                    resumo["movimentacao_liquida"]
                )
            )

            # =====================================================
            # MOVIMENTAÇÕES
            # =====================================================

            movimentos = listar_movimentacoes_periodo(
                inicio,
                fim
            )

            self.tabela_movimentos.setRowCount(0)

            for mov in movimentos:

                linha = self.tabela_movimentos.rowCount()

                self.tabela_movimentos.insertRow(
                    linha
                )

                valor = int(
                    mov["valor_centavos"]
                )

                if mov["tipo"] == "SANGRIA":

                    valor = -valor

                dados = [
                    mov["data"],
                    mov["tipo"],
                    mov["descricao"],
                    mov["forma_pagamento"] or "",
                    _money_centavos(valor),
                    mov["usuario_nome"] or "",
                    mov["observacao"] or "",
                ]

                for coluna, item in enumerate(dados):

                    self.tabela_movimentos.setItem(
                        linha,
                        coluna,
                        QTableWidgetItem(
                            str(item)
                        )
                    )

            # =====================================================
            # CAIXAS
            # =====================================================

            caixas = listar_caixas_periodo(
                inicio,
                fim
            )

            self.tabela_caixas.setRowCount(0)

            for caixa in caixas:

                linha = self.tabela_caixas.rowCount()

                self.tabela_caixas.insertRow(
                    linha
                )

                dados = [
                    caixa["id"],
                    caixa["data_abertura"] or "",
                    caixa["usuario_abertura_nome"] or "",
                    _money_centavos(
                        caixa["valor_inicial_centavos"]
                    ),
                    caixa["status"],
                    caixa["data_fechamento"] or "",
                    caixa["usuario_fechamento_nome"] or "",
                    _money_centavos(
                        caixa["valor_final_centavos"]
                    )
                    if caixa["valor_final_centavos"] is not None
                    else "",
                    _money_centavos(
                        caixa["diferenca_centavos"]
                    )
                    if caixa["diferenca_centavos"] is not None
                    else "",
                ]

                for coluna, item in enumerate(dados):

                    self.tabela_caixas.setItem(
                        linha,
                        coluna,
                        QTableWidgetItem(
                            str(item)
                        )
                    )

        except Exception as e:

            QMessageBox.critical(
                self,
                "Erro",
                str(e)
            )


if __name__ == "__main__":

    from PySide6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)

    janela = TelaRelatorioCaixa()

    janela.resize(
        1200,
        800
    )

    janela.show()

    sys.exit(
        app.exec()
    )