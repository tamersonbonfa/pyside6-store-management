from __future__ import annotations
from datetime import datetime
from typing import Any
from database.db import get_connection

def _now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def listar_produtos_ativos_para_venda() -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, nome, marca, categoria, tamanho, unidade, codigo_barras,
                   custo_centavos, preco_centavos, quantidade, estoque_minimo
            FROM produtos
            WHERE ativo = 1
            ORDER BY nome COLLATE NOCASE ASC
            """
        ).fetchall()
        return [dict(r) for r in rows]

def listar_clientes_para_venda() -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, nome, telefone, endereco
            FROM clientes
            ORDER BY nome COLLATE NOCASE ASC
            """
        ).fetchall()
        return [dict(r) for r in rows]

def criar_venda(
    usuario_id: int,
    cliente_id: int | None,
    forma_pagamento: str,
    itens: list[dict[str, Any]],
    valor_pago: float,
    observacoes: str = "",
) -> int:
    forma_pagamento = (forma_pagamento or "").strip().upper()
    if forma_pagamento not in ("DINHEIRO", "PIX", "CARTAO"):
        raise ValueError("Forma de pagamento inválida.")

    if not itens:
        raise ValueError("Adicione pelo menos 1 item.")

    if valor_pago < 0:
        raise ValueError("Valor pago inválido.")

    observacoes = (observacoes or "").strip()

    with get_connection() as conn:
        total = 0.0
        for it in itens:
            pid = int(it["produto_id"])
            qtd = int(it["quantidade"])
            preco = float(it["preco_unitario"])
            desconto = float(it.get("desconto", 0))

            row = conn.execute(
                "SELECT nome, quantidade, ativo FROM produtos WHERE id = ?", (pid,)
            ).fetchone()

            if not row or int(row["ativo"]) != 1:
                raise ValueError(f"Produto inválido ou inativo.")

            estoque_atual = int(row["quantidade"])
            if qtd > estoque_atual:
                raise ValueError(f"Estoque insuficiente para: {row['nome']}")

            subtotal = qtd * preco * (1 - desconto / 100)
            total += subtotal

        if valor_pago < total:
            raise ValueError("Valor pago insuficiente.")

        troco = float(valor_pago - total)

        usuario_row = conn.execute("SELECT nome, username FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
        usuario_nome = usuario_row["nome"] if (usuario_row and usuario_row["nome"]) else (usuario_row["username"] if usuario_row else "Desconhecido")

        cur = conn.execute(
            """
            INSERT INTO vendas (data, cliente_id, usuario_id, forma_pagamento, total, valor_pago, troco, observacoes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (_now_iso(), cliente_id, usuario_id, forma_pagamento, float(total), float(valor_pago), float(troco), observacoes),
        )
        venda_id = int(cur.lastrowid)

        for it in itens:
            pid = int(it["produto_id"])
            qtd = int(it["quantidade"])
            preco = float(it["preco_unitario"])
            desconto = float(it.get("desconto", 0))
            subtotal = qtd * preco * (1 - desconto / 100)

            produto = conn.execute("SELECT tamanho, unidade FROM produtos WHERE id = ?", (pid,)).fetchone()
            tamanho = produto["tamanho"] if produto else 0
            unidade = produto["unidade"] if produto else "un"

            # CORREÇÃO: Adicionado 'desconto' na tabela venda_itens
            conn.execute(
                """
                INSERT INTO venda_itens (venda_id, produto_id, quantidade, preco_unitario, subtotal, tamanho, unidade, desconto)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (venda_id, pid, qtd, preco, subtotal, tamanho, unidade, desconto),
            )

            conn.execute(
                """
                INSERT INTO movimentacoes_estoque
                (data, tipo, produto_id, quantidade, observacao, usuario_id, usuario_nome, venda_id, tamanho, unidade, valor_venda, desconto)
                VALUES (?, 'SAIDA', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (_now_iso(), pid, qtd, "Venda", usuario_id, usuario_nome, venda_id, tamanho, unidade, subtotal, desconto),
            )

            conn.execute("UPDATE produtos SET quantidade = quantidade - ? WHERE id = ?", (qtd, pid))

        conn.commit()
        return venda_id

def obter_dados_venda(venda_id: int) -> dict[str, Any]:
    with get_connection() as conn:
        venda = conn.execute(
            """
            SELECT v.id, v.data, v.forma_pagamento, v.total, v.valor_pago, v.troco, v.observacoes,
                   c.nome as cliente_nome, c.telefone as cliente_telefone, c.endereco as cliente_endereco,
                   u.nome as usuario_nome, u.username as usuario_user
            FROM vendas v
            LEFT JOIN clientes c ON c.id = v.cliente_id
            LEFT JOIN usuarios u ON u.id = v.usuario_id
            WHERE v.id = ?
            """,
            (int(venda_id),),
        ).fetchone()

        if not venda:
            raise ValueError("Venda não encontrada.")

        # CORREÇÃO: i.desconto adicionado explicitamente no SELECT
        itens = conn.execute(
            """
            SELECT i.quantidade, i.preco_unitario, i.subtotal, i.desconto,
                   i.tamanho, i.unidade,
                   p.nome as produto_nome, p.marca as produto_marca
            FROM venda_itens i
            JOIN produtos p ON p.id = i.produto_id
            WHERE i.venda_id = ?
            ORDER BY i.id ASC
            """,
            (int(venda_id),),
        ).fetchall()

        venda_dict = dict(venda)
        # Garantia de nome do vendedor caso o campo 'nome' esteja vazio
        if not venda_dict.get("usuario_nome"):
            venda_dict["usuario_nome"] = venda_dict.get("usuario_user") or "Desconhecido"

        return {
            "venda": venda_dict,
            "itens": [dict(r) for r in itens],
        }