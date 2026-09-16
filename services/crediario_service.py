from __future__ import annotations

from datetime import datetime
from typing import Any

from database.db import get_connection


def _now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def _centavos_para_reais(valor: int | None) -> float:
    return (valor or 0) / 100

def listar_contas_receber(
    status: str | None = None
) -> list[dict[str, Any]]:

    sql = """
        SELECT
            cr.id,
            cr.cliente_id,
            c.nome AS cliente_nome,
            cr.venda_id,
            cr.valor_centavos,
            cr.valor_pago_centavos,
            (cr.valor_centavos - cr.valor_pago_centavos) AS saldo_centavos,
            cr.status,
            cr.data_criacao,
            cr.data_quitacao,
            cr.observacao

        FROM contas_receber cr

        JOIN clientes c
            ON c.id = cr.cliente_id
    """

    params = []

    if status:
        sql += " WHERE cr.status = ? "
        params.append(status)

    sql += """
        ORDER BY cr.id DESC
    """

    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()

        return [
            {
                **dict(row),
                "valor": _centavos_para_reais(row["valor_centavos"]),
                "pago": _centavos_para_reais(row["valor_pago_centavos"]),
                "saldo": _centavos_para_reais(row["saldo_centavos"]),
            }
            for row in rows
        ]

def buscar_contas_cliente(cliente_id: int) -> list[dict[str, Any]]:

    with get_connection() as conn:

        rows = conn.execute(
            """
            SELECT
                cr.*,
                c.nome AS cliente_nome

            FROM contas_receber cr

            JOIN clientes c
                ON c.id = cr.cliente_id

            WHERE cr.cliente_id = ?

            ORDER BY cr.id DESC
            """,
            (cliente_id,)
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]
        
def registrar_pagamento(
    conta_id: int,
    valor_pago: int,
    usuario_id: int,
    observacao: str = ""
):

    with get_connection() as conn:

        conta = conn.execute(
            """
            SELECT
                valor_centavos,
                valor_pago_centavos

            FROM contas_receber

            WHERE id = ?
            """,
            (conta_id,)
        ).fetchone()


        if not conta:
            raise ValueError("Conta não encontrada.")


        novo_pago = (
            int(conta["valor_pago_centavos"])
            + int(valor_pago)
        )


        total = int(conta["valor_centavos"])


        if novo_pago >= total:
            status = "QUITADO"
            data_quitacao = _now_iso()
        elif novo_pago > 0:
            status = "PARCIAL"
            data_quitacao = None
        else:
            status = "ABERTO"
            data_quitacao = None


        conn.execute(
            """
            INSERT INTO pagamentos_contas
            (
                conta_id,
                valor_centavos,
                data,
                usuario_id,
                observacao
            )

            VALUES (?, ?, ?, ?, ?)
            """,
            (
                conta_id,
                valor_pago,
                _now_iso(),
                usuario_id,
                observacao
            )
        )


        conn.execute(
            """
            UPDATE contas_receber

            SET
                valor_pago_centavos = ?,
                status = ?,
                data_quitacao = ?

            WHERE id = ?
            """,
            (
                novo_pago,
                status,
                data_quitacao,
                conta_id
            )
        )

        conn.commit()
        
def listar_pagamentos_conta(conta_id: int) -> list[dict[str, Any]]:

    with get_connection() as conn:

        rows = conn.execute(
            """
            SELECT
                pc.id,
                pc.data,
                pc.valor_centavos,
                pc.observacao,
                u.nome AS usuario_nome

            FROM pagamentos_contas pc

            LEFT JOIN usuarios u
                ON u.id = pc.usuario_id

            WHERE pc.conta_id = ?

            ORDER BY pc.id DESC
            """,
            (conta_id,)
        ).fetchall()


        return [
            {
                **dict(row),
                "valor": _centavos_para_reais(row["valor_centavos"])
            }
            for row in rows
        ]

def listar_clientes_devedores() -> list[dict[str, Any]]:

    with get_connection() as conn:

        rows = conn.execute(
            """
            SELECT
                c.id,
                c.nome,
                c.telefone,

                COUNT(cr.id) AS quantidade_contas,

                SUM(cr.valor_centavos) AS total_devido,

                SUM(cr.valor_pago_centavos) AS total_pago,

                SUM(
                    cr.valor_centavos - cr.valor_pago_centavos
                ) AS saldo_devedor

            FROM clientes c

            JOIN contas_receber cr
                ON cr.cliente_id = c.id

            WHERE cr.status IN ('ABERTO', 'PARCIAL')

            GROUP BY c.id

            ORDER BY saldo_devedor DESC
            """
        ).fetchall()


        return [
            {
                **dict(row),

                "total_devido":
                    _centavos_para_reais(
                        row["total_devido"]
                    ),

                "total_pago":
                    _centavos_para_reais(
                        row["total_pago"]
                    ),

                "saldo_devedor":
                    _centavos_para_reais(
                        row["saldo_devedor"]
                    )
            }

            for row in rows
        ]