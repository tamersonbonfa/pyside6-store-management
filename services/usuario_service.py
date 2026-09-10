from __future__ import annotations

from typing import Any

from database.db import get_connection
from services.auth_service import hash_password

def listar_usuarios() -> list[dict[str, Any]]:
    """Retorna todos os usuários."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT id, username, nome, cargo, is_admin, ativo
            FROM usuarios
            ORDER BY username COLLATE NOCASE ASC
        """).fetchall()
        return [dict(r) for r in rows]


def buscar_usuario_por_id(usuario_id: int) -> dict[str, Any] | None:
    """Busca um usuário pelo ID."""
    with get_connection() as conn:
        row = conn.execute("""
            SELECT id, username, nome, cargo, is_admin, ativo
            FROM usuarios
            WHERE id = ?
        """, (usuario_id,)).fetchone()
        return dict(row) if row else None


def criar_usuario(username: str, nome: str, cargo: str, senha: str, is_admin: bool = False, ativo: bool = True) -> int:
    """Cria um novo usuário."""
    username = username.strip() if username else ""
    nome = nome.strip() if nome else ""
    cargo = cargo.strip() if cargo else ""

    if not username or not nome or not senha or not cargo:
        raise ValueError("Username, nome, cargo e senha são obrigatórios.")

    senha_hash = hash_password(senha)

    with get_connection() as conn:
        cur = conn.execute("""
            INSERT INTO usuarios (username, nome, cargo, senha_hash, is_admin, ativo)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (username, nome, cargo, senha_hash, 1 if is_admin else 0, 1 if ativo else 0))
        conn.commit()
        return int(cur.lastrowid)


def atualizar_usuario(usuario_id: int, username: str, nome: str, cargo: str, senha: str | None = None, is_admin: bool = False, ativo: bool = True):
    """Atualiza um usuário existente. Se senha for None, não altera a senha."""
    username = username.strip() if username else ""
    nome = nome.strip() if nome else ""
    cargo = cargo.strip() if cargo else ""

    if not username or not nome or not cargo:
        raise ValueError("Username, nome e cargo são obrigatórios.")

    with get_connection() as conn:
        if senha:
            senha_hash = hash_password(senha)
            cursor = conn.execute("""
                UPDATE usuarios
                SET username = ?, nome = ?, cargo = ?, senha_hash = ?, is_admin = ?, ativo = ?
                WHERE id = ?
            """, (username, nome, cargo, senha_hash, 1 if is_admin else 0, 1 if ativo else 0, usuario_id))
        else:
            cursor = conn.execute("""
                UPDATE usuarios
                SET username = ?, nome = ?, cargo = ?, is_admin = ?, ativo = ?
                WHERE id = ?
            """, (username, nome, cargo, 1 if is_admin else 0, 1 if ativo else 0, usuario_id))
            
        if cursor.rowcount == 0:
            raise ValueError("Usuário não encontrado.")
        
        conn.commit()
        return True

def existe_usuario_admin() -> bool:
    with get_connection() as conn:
        row = conn.execute("""
            SELECT id
            FROM usuarios
            WHERE is_admin = 1
            LIMIT 1
        """).fetchone()

        return row is not None