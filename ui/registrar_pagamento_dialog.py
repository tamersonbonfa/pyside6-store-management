from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QDoubleSpinBox,
    QTextEdit,
    QPushButton,
    QHBoxLayout,
    QMessageBox
)


class RegistrarPagamentoDialog(QDialog):

    def __init__(
        self,
        saldo: float,
        parent=None
    ):
        super().__init__(parent)

        self.setWindowTitle(
            "Registrar pagamento"
        )

        self.resize(350, 250)

        self.valor = 0
        self.observacao = ""

        layout = QVBoxLayout(self)


        lbl = QLabel(
            f"Saldo pendente: R$ {saldo:.2f}"
        )

        lbl.setStyleSheet(
            "font-size:16px;font-weight:bold;"
        )

        layout.addWidget(lbl)


        layout.addWidget(
            QLabel("Valor recebido:")
        )


        self.sp_valor = QDoubleSpinBox()

        self.sp_valor.setRange(
            0,
            saldo
        )

        self.sp_valor.setDecimals(2)

        self.sp_valor.setPrefix(
            "R$ "
        )

        layout.addWidget(
            self.sp_valor
        )


        layout.addWidget(
            QLabel("Observação:")
        )


        self.txt_obs = QTextEdit()

        self.txt_obs.setFixedHeight(
            70
        )

        layout.addWidget(
            self.txt_obs
        )


        botoes = QHBoxLayout()

        self.btn_ok = QPushButton(
            "Confirmar"
        )

        self.btn_cancelar = QPushButton(
            "Cancelar"
        )


        botoes.addWidget(
            self.btn_ok
        )

        botoes.addWidget(
            self.btn_cancelar
        )

        layout.addLayout(
            botoes
        )


        self.btn_ok.clicked.connect(
            self.confirmar
        )

        self.btn_cancelar.clicked.connect(
            self.reject
        )


    def confirmar(self):

        if self.sp_valor.value() <= 0:
            QMessageBox.warning(
                self,
                "Aviso",
                "Informe um valor válido."
            )
            return


        self.valor = self.sp_valor.value()

        self.observacao = (
            self.txt_obs
            .toPlainText()
            .strip()
        )

        self.accept()