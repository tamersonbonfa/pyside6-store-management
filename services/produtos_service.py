from __future__ import annotations
from datetime import datetime
from typing import Any
from database.db import get_connection

def _now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def listar_produtos(apenas_ativos: bool = True) -> list[dict[str, Any]]:
    sql = """
    SELECT id, nome, marca, categoria, tamanho, unidade, codigo_barras, custo_centavos, preco_centavos, quantidade, estoque_minimo, ativo, criado_em
    FROM produtos
    """
    params = []

    if apenas_ativos:
        sql += " WHERE ativo = 1 "

    sql += " ORDER BY nome COLLATE NOCASE ASC "

    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]


def buscar_produtos_por_nome(texto: str, apenas_ativos: bool = True) -> list[dict[str, Any]]:
    texto = (texto or "").strip()
    if not texto:
        return listar_produtos(apenas_ativos=apenas_ativos)

    sql = """
    SELECT id, nome, marca, categoria, tamanho, unidade, codigo_barras, custo, preco_venda,
           quantidade, estoque_minimo, ativo, criado_em
    FROM produtos
    WHERE (nome LIKE ? OR marca LIKE ? OR categoria LIKE ? OR codigo_barras LIKE ?)
    """
    params = [f"%{texto}%", f"%{texto}%", f"%{texto}%", f"%{texto}%"]

    if apenas_ativos:
        sql += " AND ativo = 1 "

    sql += " ORDER BY nome COLLATE NOCASE ASC "

    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]


def criar_produto(
    nome: str,
    marca: str,
    categoria: str,
    tamanho: float,
    unidade: str,
    custo: float,
    preco_venda: float,
    quantidade: int,
    estoque_minimo: int,
    codigo_barras: str = "",
    ativo: int = 1,
    usuario_id: int | None = None
) -> int:
    nome = (nome or "").strip()
    marca = (marca or "").strip()
    categoria = (categoria or "").strip()
    unidade = (unidade or "").strip()
    codigo_barras = (codigo_barras or "").strip()

    if not nome:
        raise ValueError("Nome do produto é obrigatório.")
    
    # Sanitização básica
    tamanho = max(0, float(tamanho or 0))
    quantidade = max(0, int(quantidade or 0))
    estoque_minimo = max(0, int(estoque_minimo or 0))

    with get_connection() as conn:
        # --- VERIFICAÇÃO DE USUÁRIO (Evita erro de Foreign Key) ---
        # Se usuario_id for 0 ou None, tentamos o ID 1, ou deixamos None
        if not usuario_id or usuario_id == 0:
            usuario_id = 1 # Geralmente o ID do primeiro admin
        
        usuario_row = conn.execute("SELECT nome, username FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
        
        if usuario_row:
            usuario_nome = usuario_row["nome"] if usuario_row["nome"] else usuario_row["username"]
        else:
            # Se o usuário ID 1 também não existir, setamos None para não quebrar a FK
            usuario_id = None
            usuario_nome = "Sistema"

        # 1. Insere o Produto
        cur = conn.execute(
            """
            INSERT INTO produtos
            (nome, marca, categoria, tamanho, unidade, codigo_barras, custo, preco_venda, quantidade, estoque_minimo, ativo, criado_em)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (nome, marca, categoria, tamanho, unidade, codigo_barras,
             float(custo), float(preco_venda), quantidade, estoque_minimo, ativo, _now_iso())
        )
        produto_id = int(cur.lastrowid)

        # 2. Registra Movimentação Inicial (apenas se houver quantidade)
        if quantidade > 0:
            conn.execute(
                """
                INSERT INTO movimentacoes_estoque
                (data, tipo, produto_id, quantidade, observacao, usuario_id, usuario_nome, venda_id, tamanho, unidade)
                VALUES (?, 'ENTRADA', ?, ?, ?, ?, ?, NULL, ?, ?)
                """,
                (_now_iso(), produto_id, quantidade, "Estoque inicial", usuario_id, usuario_nome, tamanho, unidade)
            )
            
        conn.commit()
        return produto_id


def atualizar_produto(
    produto_id: int,
    nome: str,
    marca: str,
    categoria: str,
    tamanho: float,
    unidade: str,
    custo: float,
    preco_venda: float,
    estoque_minimo: int,
    ativo: bool,
    codigo_barras: str = "",
) -> None:
    nome = (nome or "").strip()
    marca = (marca or "").strip()
    categoria = (categoria or "").strip()
    unidade = (unidade or "").strip()
    codigo_barras = (codigo_barras or "").strip()

    if not nome:
        raise ValueError("Nome do produto é obrigatório.")

    with get_connection() as conn:
        conn.execute(
            """
            UPDATE produtos
            SET nome = ?, marca = ?, categoria = ?, tamanho = ?, unidade = ?, codigo_barras = ?,
                custo = ?, preco_venda = ?, estoque_minimo = ?, ativo = ?
            WHERE id = ?
            """,
            (
                nome,
                marca,
                categoria,
                float(tamanho),
                unidade,
                codigo_barras,
                float(custo),
                float(preco_venda),
                int(estoque_minimo),
                1 if ativo else 0,
                int(produto_id),
            ),
        )
        conn.commit()


def registrar_entrada_estoque(produto_id: int, quantidade: int, observacao: str, usuario_id: int | None = None):
    if quantidade <= 0:
        raise ValueError("Quantidade deve ser maior que 0.")

    observacao = (observacao or "").strip()
    usuario_id = usuario_id or 0

    with get_connection() as conn:
        produto = conn.execute("SELECT tamanho, unidade FROM produtos WHERE id = ?", (produto_id,)).fetchone()
        if not produto:
            raise ValueError("Produto não encontrado.")
        tamanho = float(produto["tamanho"])
        unidade = produto["unidade"]

        # Obtém nome do usuário
        usuario_row = conn.execute("SELECT nome, username FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
        usuario_nome = usuario_row["nome"] if usuario_row and usuario_row["nome"] else (usuario_row["username"] if usuario_row else "Desconhecido")

        conn.execute(
            "UPDATE produtos SET quantidade = quantidade + ? WHERE id = ?",
            (int(quantidade), int(produto_id)),
        )
        conn.execute(
            """
            INSERT INTO movimentacoes_estoque
            (data, tipo, produto_id, quantidade, observacao, usuario_id, usuario_nome, venda_id, tamanho, unidade)
            VALUES (?, 'ENTRADA', ?, ?, ?, ?, ?, NULL, ?, ?)
            """,
            (_now_iso(), int(produto_id), int(quantidade), observacao, usuario_id, usuario_nome, tamanho, unidade),
        )
        conn.commit()


def registrar_ajuste_estoque(produto_id: int, nova_quantidade: int, observacao: str, usuario_id: int | None = None):
    if nova_quantidade < 0:
        raise ValueError("Quantidade não pode ser negativa.")

    observacao = (observacao or "").strip()
    usuario_id = usuario_id or 0

    with get_connection() as conn:
        row = conn.execute("SELECT quantidade, tamanho, unidade FROM produtos WHERE id = ?", (int(produto_id),)).fetchone()
        if not row:
            raise ValueError("Produto não encontrado.")

        atual = int(row["quantidade"])
        diff = int(nova_quantidade) - atual
        tamanho = float(row["tamanho"])
        unidade = row["unidade"]

        # Obtém nome do usuário
        usuario_row = conn.execute("SELECT nome, username FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
        usuario_nome = usuario_row["nome"] if usuario_row and usuario_row["nome"] else (usuario_row["username"] if usuario_row else "Desconhecido")

        conn.execute(
            "UPDATE produtos SET quantidade = ? WHERE id = ?",
            (int(nova_quantidade), int(produto_id))
        )
        conn.execute(
            """
            INSERT INTO movimentacoes_estoque
            (data, tipo, produto_id, quantidade, observacao, usuario_id, usuario_nome, venda_id, tamanho, unidade)
            VALUES (?, 'AJUSTE', ?, ?, ?, ?, ?, NULL, ?, ?)
            """,
            (_now_iso(), int(produto_id), int(diff), observacao or "Ajuste de estoque", usuario_id, usuario_nome, tamanho, unidade)
        )
        conn.commit()


def listar_movimentacoes(produto_id: int | None = None, limite: int = 200) -> list[dict[str, Any]]:
    sql = """
        SELECT 
            m.*, 
            p.nome as produto_nome, 
            p.categoria,       -- << ADICIONE ESTA LINHA
            p.tamanho, 
            p.unidade,
            u.nome as usuario_nome
        FROM movimentacoes_estoque m
        LEFT JOIN produtos p ON m.produto_id = p.id
        LEFT JOIN usuarios u ON m.usuario_id = u.id
    """
    params = []

    if produto_id:
        sql += " WHERE m.produto_id = ? "
        params.append(int(produto_id))

    sql += " ORDER BY m.id DESC LIMIT ? "
    params.append(int(limite))

    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]


def registrar_movimentacao_saida(produto_id: int, quantidade: int, usuario_id: int | None, venda_id: int | None = None,
                                 observacao: str = "Saída", valor_venda: float = 0, desconto: float = 0):
    """
    Registra uma saída no estoque.
    """
    usuario_id = usuario_id or 0
    valor_venda = float(valor_venda or 0)
    desconto = float(desconto or 0)
    venda_id = venda_id or None
    observacao = (observacao or "").strip() or "Saída"

    data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_connection() as conn:
        produto = conn.execute("SELECT tamanho, unidade FROM produtos WHERE id = ?", (produto_id,)).fetchone()
        tamanho = float(produto["tamanho"]) if produto else 0
        unidade = produto["unidade"] if produto else "un"

        # insere movimentação
        conn.execute("""
            INSERT INTO movimentacoes_estoque
            (data, tipo, produto_id, quantidade, observacao, usuario_id, venda_id, valor_venda, desconto, tamanho, unidade)
            VALUES (?, 'SAIDA', ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (data, produto_id, quantidade, observacao, usuario_id, venda_id, valor_venda, desconto, tamanho, unidade))

        # baixa estoque
        conn.execute("UPDATE produtos SET quantidade = quantidade - ? WHERE id = ?", (quantidade, produto_id))
        conn.commit()
