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
    QInputDialog,
)

from services.caixa_service import (
    saldo_caixa,
    listar_movimentacoes_caixa,
    registrar_entrada_caixa,
    registrar_saida_caixa,
    abrir_caixa,
    fechar_caixa,
    obter_caixa_aberto
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

        self.btn_abrir = QPushButton(
            "🟢 Abrir Caixa"
        )

        self.btn_fechar = QPushButton(
            "🔴 Fechar Caixa"
        )


        barra.addWidget(
            self.btn_atualizar
        )

        barra.addWidget(
            self.btn_abrir
        )

        barra.addWidget(
            self.btn_fechar
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

        self.btn_sangria.clicked.connect(
            self.abrir_sangria
        )

        self.btn_entrada.clicked.connect(
            self.abrir_entrada_manual
        )

        self.btn_abrir.clicked.connect(
            self.abrir_caixa
        )

        self.btn_fechar.clicked.connect(
            self.fechar_caixa
        )

        self.carregar()


    def carregar(self):

        try:

            saldo = saldo_caixa()

            caixa = obter_caixa_aberto()


            if caixa:

                status = "🟢 Caixa aberto"

            else:

                status = "🔴 Caixa fechado"


            self.lbl_saldo.setText(
                f"{status}\nSaldo: {_money(saldo / 100)}"
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
            
    def abrir_sangria(self):

        valor, ok = QInputDialog.getDouble(
            self,
            "Sangria",
            "Valor retirado:"
        )

        if not ok:
            return

        if valor <= 0:
            return

        try:
            registrar_saida_caixa(
                valor_centavos=int(round(valor * 100)),
                descricao="Sangria",
                usuario_id=self.usuario_id
            )

            QMessageBox.information(
                self,
                "Sucesso",
                "Sangria registrada."
            )

            self.carregar()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Erro",
                str(e)
            )
            
    def abrir_entrada_manual(self):

        valor, ok = QInputDialog.getDouble(
            self,
            "Entrada Manual",
            "Valor:"
        )

        if not ok:
            return

        if valor <= 0:
            return

        try:
            registrar_entrada_caixa(
                valor_centavos=int(round(valor * 100)),
                descricao="Entrada manual",
                usuario_id=self.usuario_id
            )

            QMessageBox.information(
                self,
                "Sucesso",
                "Entrada registrada."
            )

            self.carregar()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Erro",
                str(e)
            )
            
    def abrir_caixa(self):

        valor, ok = QInputDialog.getDouble(
            self,
            "Abrir Caixa",
            "Valor inicial:"
        )

        if not ok:
            return


        try:

            abrir_caixa(
                usuario_id=self.usuario_id,
                valor_inicial_centavos=int(round(valor * 100))
            )


            QMessageBox.information(
                self,
                "Sucesso",
                "Caixa aberto."
            )


            self.carregar()


        except Exception as e:

            QMessageBox.critical(
                self,
                "Erro",
                str(e)
            )
            
    def fechar_caixa(self):

        valor, ok = QInputDialog.getDouble(
            self,
            "Fechar Caixa",
            "Valor contado:"
        )


        if not ok:
            return


        try:

            fechar_caixa(
                usuario_id=self.usuario_id,
                valor_final_centavos=int(round(valor * 100))
            )


            QMessageBox.information(
                self,
                "Sucesso",
                "Caixa fechado."
            )


            self.carregar()


        except Exception as e:

            QMessageBox.critical(
                self,
                "Erro",
                str(e)
            )