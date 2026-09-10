from __future__ import annotations
import sqlite3
import os
import sys
from pathlib import Path

# 1. DEFINIÇÃO DE CAMINHOS DINÂMICOS
if hasattr(sys, '_MEIPASS'):
    # Se estiver rodando como executável (.exe)
    # O Schema (SQL) fica dentro do pacote extraído temporariamente
    BASE_DIR_INTERNO = Path(sys._MEIPASS)
    SCHEMA_PATH = BASE_DIR_INTERNO / "database" / "schema.sql"
    
    # O Banco de Dados deve ficar na pasta REAL onde o .exe está localizado
    DIRETORIO_EXE = Path(os.path.dirname(os.path.abspath(sys.argv[0])))
    DB_PATH = DIRETORIO_EXE / "database.db"
else:
    # Se estiver rodando como script Python normal
    BASE_DIR_LOCAL = Path(__file__).resolve().parent
    SCHEMA_PATH = BASE_DIR_LOCAL / "schema.sql"
    DB_PATH = BASE_DIR_LOCAL / "database.db"

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(
        DB_PATH,
        timeout=10
    )

    conn.row_factory = sqlite3.Row

    conn.execute(
        "PRAGMA foreign_keys = ON;"
    )

    conn.execute(
        "PRAGMA journal_mode=WAL;"
    )

    return conn

def init_db():
    # Garante que a pasta do banco existe (útil se o banco estiver em subpastas)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with get_connection() as conn:
        try:
            # Lê o schema do local interno (onde o PyInstaller guardou)
            schema = SCHEMA_PATH.read_text(encoding="utf-8")
            conn.executescript(schema)
            conn.commit()
        except FileNotFoundError as e:
            raise RuntimeError(
                "Arquivo schema.sql não encontrado."
            ) from e
        except Exception as e:
            raise RuntimeError(
                "Falha ao inicializar banco de dados."
            ) from e