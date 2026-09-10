from __future__ import annotations

import bcrypt

from dataclasses import dataclass
from database.db import get_connection



def hash_password(password: str) -> str:
    # Gera o salt e o hash. O 'cost' padrão é 12.
    # O retorno já inclui o salt necessário para a verificação futura.
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # O bcrypt extrai o salt automaticamente do hash armazenado
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), 
        hashed_password.encode("utf-8")
    )

@dataclass
class Usuario:
    id: int
    username: str
    nome: str | None
    cargo: str
    is_admin: bool


def authenticate(username: str, password: str) -> Usuario | None:
    username = (username or "").strip()
    password = (password or "").strip()
    
    if not username or not password:
        return None

    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, username, nome, cargo, senha_hash, is_admin, ativo
            FROM usuarios
            WHERE username = ?
            """,
            (username,),
        ).fetchone()

        if not row:
            return None

        if int(row["ativo"]) != 1:
            return None

        if not verify_password(password, row["senha_hash"]):
            return None
        conn.execute(
            """
            UPDATE usuarios
            SET ultimo_login = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (row["id"],)
        )
        conn.commit()

        return Usuario(
            id=int(row["id"]),
            username=str(row["username"]),
            nome=str(row["nome"]),
            cargo=str(row["cargo"]),
            is_admin=bool(row["is_admin"]),
        )
