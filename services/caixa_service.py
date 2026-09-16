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

    caixa_id = verificar_caixa_aberto()

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
                caixa_id,
                observacao
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                caixa_id,
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

        caixa = conn.execute(
            """
            SELECT id
            FROM caixas
            WHERE status = 'ABERTO'
            """
        ).fetchone()


        if not caixa:
            return 0


        saldo = conn.execute(
            """
            SELECT COALESCE(
                SUM(
                    CASE
                        WHEN tipo IN (
                            'ABERTURA',
                            'VENDA',
                            'RECEBIMENTO_CREDIARIO',
                            'AJUSTE'
                        )
                        THEN valor_centavos

                        WHEN tipo = 'SANGRIA'
                        THEN -valor_centavos

                        ELSE 0
                    END
                ),
                0
            )

            FROM caixa_movimentacoes

            WHERE caixa_id = ?
            """,
            (caixa["id"],)
        ).fetchone()[0]


        return int(saldo)

def registrar_saida_caixa(
    valor_centavos: int,
    descricao: str,
    usuario_id: int,
    observacao: str = "",
    tipo: str = "SANGRIA"
):

    caixa_id = verificar_caixa_aberto()
    
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
                caixa_id,
                observacao
            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                caixa_id,
                observacao
            )
        )

        conn.commit()
        
def registrar_entrada_caixa(
    valor_centavos: int,
    descricao: str,
    usuario_id: int,
    observacao: str = ""
):

    caixa_id = verificar_caixa_aberto()
    
    if valor_centavos <= 0:
        raise ValueError(
            "O valor da entrada deve ser maior que zero."
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
                caixa_id,
                observacao
            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                _now_iso(),
                "AJUSTE",
                descricao,
                valor_centavos,
                None,
                None,
                None,
                usuario_id,
                caixa_id,
                observacao
            )
        )

        conn.commit()
        
def abrir_caixa(
    usuario_id: int,
    valor_inicial_centavos: int
):

    with get_connection() as conn:

        caixa_aberto = conn.execute(
            """
            SELECT id
            FROM caixas
            WHERE status = 'ABERTO'
            """
        ).fetchone()


        if caixa_aberto:
            raise ValueError(
                "Já existe um caixa aberto."
            )


        cursor = conn.execute(
            """
            INSERT INTO caixas
            (
                usuario_abertura,
                data_abertura,
                valor_inicial_centavos,
                status
            )
            VALUES (?, ?, ?, 'ABERTO')
            """,
            (
                usuario_id,
                _now_iso(),
                valor_inicial_centavos
            )
        )


        caixa_id = cursor.lastrowid


        conn.execute(
            """
            INSERT INTO caixa_movimentacoes
            (
                data,
                tipo,
                descricao,
                valor_centavos,
                caixa_id,
                usuario_id
            )

            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                _now_iso(),
                "ABERTURA",
                "Abertura do caixa",
                valor_inicial_centavos,
                caixa_id,
                usuario_id
            )
        )


        conn.commit()
        
def obter_caixa_aberto():

    with get_connection() as conn:

        return conn.execute(
            """
            SELECT *
            FROM caixas
            WHERE status = 'ABERTO'
            """
        ).fetchone()

def fechar_caixa(
    usuario_id: int,
    valor_final_centavos: int
):

    if valor_final_centavos < 0:
        raise ValueError(
            "Valor final inválido."
        )


    with get_connection() as conn:

        caixa = conn.execute(
            """
            SELECT id
            FROM caixas
            WHERE status = 'ABERTO'
            """
        ).fetchone()


        if not caixa:
            raise ValueError(
                "Não existe caixa aberto."
            )


        # saldo esperado do sistema
        saldo_esperado = saldo_caixa()


        diferenca = (
            valor_final_centavos
            - saldo_esperado
        )


        conn.execute(
            """
            UPDATE caixas

            SET
                usuario_fechamento = ?,
                data_fechamento = ?,
                valor_final_centavos = ?,
                diferenca_centavos = ?,
                status = 'FECHADO'

            WHERE id = ?
            """,
            (
                usuario_id,
                _now_iso(),
                valor_final_centavos,
                diferenca,
                caixa["id"]
            )
        )


        conn.commit()

def verificar_caixa_aberto():

    with get_connection() as conn:

        caixa = conn.execute(
            """
            SELECT id
            FROM caixas
            WHERE status = 'ABERTO'
            """
        ).fetchone()


        if not caixa:
            raise ValueError(
                "Não existe caixa aberto."
            )


        return caixa["id"]