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

        caixa_id = caixa["id"]

        # Saldo que o sistema espera encontrar
        saldo_esperado = saldo_caixa()

        # Diferença entre o valor contado e o esperado
        diferenca = (
            valor_final_centavos
            - saldo_esperado
        )

        data_fechamento = _now_iso()

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
                data_fechamento,
                valor_final_centavos,
                diferenca,
                caixa_id
            )
        )

        conn.commit()

        return {
            "caixa_id": caixa_id,
            "saldo_esperado": saldo_esperado,
            "valor_final": valor_final_centavos,
            "diferenca": diferenca,
        }



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


def resumo_relatorio_caixa(
    inicio: str,
    fim: str
) -> dict[str, int]:

    inicio_full = f"{inicio} 00:00:00"
    fim_full = f"{fim} 23:59:59"

    with get_connection() as conn:

        row = conn.execute(
            """
            SELECT
                COALESCE(
                    SUM(
                        CASE
                            WHEN tipo = 'ABERTURA'
                            THEN valor_centavos
                            ELSE 0
                        END
                    ),
                    0
                ) AS abertura,

                COALESCE(
                    SUM(
                        CASE
                            WHEN tipo = 'VENDA'
                            THEN valor_centavos
                            ELSE 0
                        END
                    ),
                    0
                ) AS vendas,

                COALESCE(
                    SUM(
                        CASE
                            WHEN tipo = 'RECEBIMENTO_CREDIARIO'
                            THEN valor_centavos
                            ELSE 0
                        END
                    ),
                    0
                ) AS recebimentos_crediario,

                COALESCE(
                    SUM(
                        CASE
                            WHEN tipo = 'AJUSTE'
                            THEN valor_centavos
                            ELSE 0
                        END
                    ),
                    0
                ) AS entradas,

                COALESCE(
                    SUM(
                        CASE
                            WHEN tipo = 'SANGRIA'
                            THEN valor_centavos
                            ELSE 0
                        END
                    ),
                    0
                ) AS sangrias

            FROM caixa_movimentacoes

            WHERE data BETWEEN ? AND ?
            """,
            (
                inicio_full,
                fim_full
            )
        ).fetchone()

        abertura = int(row["abertura"])
        vendas = int(row["vendas"])
        recebimentos_crediario = int(
            row["recebimentos_crediario"]
        )
        entradas = int(row["entradas"])
        sangrias = int(row["sangrias"])

        total_entradas = (
            abertura
            + vendas
            + recebimentos_crediario
            + entradas
        )

        total_saidas = sangrias

        movimentacao_liquida = (
            total_entradas
            - total_saidas
        )

        return {
            "abertura": abertura,
            "vendas": vendas,
            "recebimentos_crediario": recebimentos_crediario,
            "entradas": entradas,
            "sangrias": sangrias,
            "total_entradas": total_entradas,
            "total_saidas": total_saidas,
            "movimentacao_liquida": movimentacao_liquida,
        }
        
def listar_movimentacoes_periodo(
    inicio: str,
    fim: str
) -> list[dict[str, Any]]:

    inicio_full = f"{inicio} 00:00:00"
    fim_full = f"{fim} 23:59:59"

    with get_connection() as conn:

        rows = conn.execute(
            """
            SELECT
                cm.id,
                cm.data,
                cm.tipo,
                cm.descricao,
                cm.valor_centavos,
                cm.forma_pagamento,
                cm.venda_id,
                cm.conta_receber_id,
                cm.caixa_id,
                cm.usuario_id,
                cm.observacao,
                u.nome AS usuario_nome

            FROM caixa_movimentacoes cm

            LEFT JOIN usuarios u
                ON u.id = cm.usuario_id

            WHERE cm.data BETWEEN ? AND ?

            ORDER BY cm.data DESC, cm.id DESC
            """,
            (
                inicio_full,
                fim_full
            )
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]
        
def listar_caixas_periodo(
    inicio: str,
    fim: str
) -> list[dict[str, Any]]:

    inicio_full = f"{inicio} 00:00:00"
    fim_full = f"{fim} 23:59:59"

    with get_connection() as conn:

        rows = conn.execute(
            """
            SELECT
                cx.id,
                cx.usuario_abertura,
                ua.nome AS usuario_abertura_nome,
                cx.data_abertura,
                cx.valor_inicial_centavos,
                cx.status,
                cx.usuario_fechamento,
                uf.nome AS usuario_fechamento_nome,
                cx.data_fechamento,
                cx.valor_final_centavos,
                cx.diferenca_centavos

            FROM caixas cx

            LEFT JOIN usuarios ua
                ON ua.id = cx.usuario_abertura

            LEFT JOIN usuarios uf
                ON uf.id = cx.usuario_fechamento

            WHERE
                (
                    cx.data_abertura BETWEEN ? AND ?
                )
                OR
                (
                    cx.data_fechamento BETWEEN ? AND ?
                )

            ORDER BY cx.id DESC
            """,
            (
                inicio_full,
                fim_full,
                inicio_full,
                fim_full
            )
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]