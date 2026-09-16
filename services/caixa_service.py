from __future__ import annotations

from datetime import datetime
from typing import Any

from database.db import get_connection


def _now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def registrar_movimento_caixa(
    tipo: str,
    valor_centavos: int,
    usuario_id: int,
    descricao: str,
    forma_pagamento: str | None = None,
    venda_id: int | None = None,
    conta_receber_id: int | None = None,
    observacao: str = "",
):
    """
    Registra qualquer movimentação financeira do caixa.
    """

    if valor_centavos <= 0:
        raise ValueError(
            "O valor deve ser maior que zero."
        )

    tipos_validos = (
        "ABERTURA",
        "VENDA",
        "RECEBIMENTO_CREDIARIO",
        "SANGRIA",
        "AJUSTE",
    )

    if tipo not in tipos_validos:
        raise ValueError(
            "Tipo de movimentação inválido."
        )


    with get_connection() as conn:

        conn.execute(
            """
            INSERT INTO caixa_movimentacoes
            (
                data,
                tipo,
                descricao,
                valor_centavos,
                forma_pagamento,
                venda_id,
                conta_receber_id,
                usuario_id,
                observacao
            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                _now_iso(),
                tipo,
                descricao,
                valor_centavos,
                forma_pagamento,
                venda_id,
                conta_receber_id,
                usuario_id,
                observacao,
            )
        )

        conn.commit()



def listar_movimentacoes_caixa() -> list[dict[str, Any]]:

    with get_connection() as conn:

        rows = conn.execute(
            """
            SELECT
                cm.*,
                u.nome AS usuario_nome

            FROM caixa_movimentacoes cm

            LEFT JOIN usuarios u
                ON u.id = cm.usuario_id

            ORDER BY cm.id DESC
            """
        ).fetchall()


        return [
            dict(row)
            for row in rows
        ]



def saldo_caixa() -> int:

    with get_connection() as conn:

        entradas = conn.execute(
            """
            SELECT COALESCE(
                SUM(valor_centavos),
                0
            )

            FROM caixa_movimentacoes

            WHERE tipo IN (
                'ABERTURA',
                'VENDA',
                'RECEBIMENTO_CREDIARIO',
                'AJUSTE'
            )
            """
        ).fetchone()[0]


        saidas = conn.execute(
            """
            SELECT COALESCE(
                SUM(valor_centavos),
                0
            )

            FROM caixa_movimentacoes

            WHERE tipo = 'SANGRIA'
            """
        ).fetchone()[0]


        return int(entradas) - int(saidas)

def registrar_saida_caixa(
    valor_centavos: int,
    descricao: str,
    usuario_id: int,
    observacao: str = "",
    tipo: str = "SAIDA"
):

    if valor_centavos <= 0:
        raise ValueError(
            "O valor da saída deve ser maior que zero."
        )

    descricao = (descricao or "").strip()

    if not descricao:
        raise ValueError(
            "Informe uma descrição para a saída."
        )


    with get_connection() as conn:

        conn.execute(
            """
            INSERT INTO caixa_movimentacoes
            (
                data,
                tipo,
                descricao,
                valor_centavos,
                forma_pagamento,
                venda_id,
                conta_receber_id,
                usuario_id,
                observacao
            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                _now_iso(),
                tipo,
                descricao,
                valor_centavos,
                "DINHEIRO",
                None,
                None,
                usuario_id,
                observacao
            )
        )

        conn.commit()