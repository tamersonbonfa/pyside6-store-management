from __future__ import annotations

from datetime import datetime
from typing import Any

from database.db import get_connection


def _now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def listar_clientes() -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, nome, telefone, endereco, observacoes, ativo, criado_em
            FROM clientes
            ORDER BY nome COLLATE NOCASE ASC
            """
        ).fetchall()
        return [dict(r) for r in rows]


def buscar_clientes(texto: str) -> list[dict[str, Any]]:
    texto = (texto or "").strip()
    if not texto:
        return listar_clientes()

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, nome, telefone, endereco, observacoes, ativo, criado_em
            FROM clientes
            WHERE ativo = 1
            AND (nome LIKE ? OR telefone LIKE ?)
            ORDER BY nome COLLATE NOCASE ASC
            """,
            (f"%{texto}%", f"%{texto}%"),
        ).fetchall()
        return [dict(r) for r in rows]


def criar_cliente(nome: str, telefone: str, endereco: str, observacoes: str) -> int:
    nome = (nome or "").strip()
    telefone = (telefone or "").strip()
    endereco = (endereco or "").strip()
    observacoes = (observacoes or "").strip()

    if not nome:
        raise ValueError("Nome do cliente é obrigatório.")

    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO clientes 
            (nome, telefone, endereco, observacoes, ativo, criado_em)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (nome, telefone, endereco, observacoes, 1, _now_iso()),
        )
        conn.commit()
        return int(cur.lastrowid)


def atualizar_cliente(
    cliente_id: int,
    nome: str,
    telefone: str,
    endereco: str,
    observacoes: str,
    ativo: bool = True
) -> None:
    nome = (nome or "").strip()
    telefone = (telefone or "").strip()
    endereco = (endereco or "").strip()
    observacoes = (observacoes or "").strip()

    if not nome:
        raise ValueError("Nome do cliente é obrigatório.")

    with get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE clientes
            SET nome = ?,
                telefone = ?,
                endereco = ?,
                observacoes = ?,
                ativo = ?
            WHERE id = ?
            """,
            (
                nome,
                telefone,
                endereco,
                observacoes,
                1 if ativo else 0,
                int(cliente_id),
            ),
        )

        if cursor.rowcount == 0:
            raise ValueError("Cliente não encontrado.")

        conn.commit()
