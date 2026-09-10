from __future__ import annotations
import sqlite3 # Importação necessária para o Row
from typing import Any
from database.db import get_connection

class RelatoriosService:
    
    @staticmethod
    def resumo_detalhado(inicio: str, fim: str) -> dict[str, Any]:
        inicio_full = f"{inicio} 00:00:00"
        fim_full = f"{fim} 23:59:59"

        with get_connection() as conn:
            conn.row_factory = sqlite3.Row
            
            # 1. FINANCEIRO: Soma direto das movimentações de SAÍDA (garante que bata com o histórico)
            financeiro = conn.execute("""
                SELECT 
                    COUNT(DISTINCT venda_id) as total_vendas,
                    COALESCE(SUM(valor_venda), 0) / 100.0 as faturamento,
                    CASE 
                        WHEN COUNT(DISTINCT venda_id) > 0 
                        THEN (SUM(valor_venda) / 100.0) / COUNT(DISTINCT venda_id) 
                        ELSE 0 
                    END as ticket_medio
                FROM movimentacoes_estoque 
                WHERE tipo = 'SAIDA' AND data BETWEEN ? AND ?
            """, (inicio_full, fim_full)).fetchone()
            
            # 2. MEIOS DE PAGAMENTO (Continua vindo da tabela vendas)
            pagamentos = conn.execute("""
                SELECT forma_pagamento, SUM(total_centavos) as total
                FROM vendas
                WHERE data BETWEEN ? AND ?
                GROUP BY forma_pagamento
            """, (inicio_full, fim_full)).fetchall()

            # 3. DETALHAMENTO: Pega direto da MOVIMENTAÇÃO
            # Aqui não tem erro: se saiu no estoque, aparece aqui.
            produtos = conn.execute("""
                SELECT 
                    p.nome, 
                    m.tamanho,
                    m.unidade,
                    p.custo_centavos AS custo_centavos,
                    p.preco_centavos AS preco_centavos,
                    CAST(SUM(m.quantidade) AS INTEGER) as qtd_vendida, 
                    SUM(m.valor_venda) / 100.0 AS total_faturado,
                    0 as desconto_total_reais, -- Ajuste se você salvar desconto na movimentação
                    (
                        SUM(m.valor_venda) -
                        SUM(m.quantidade * p.custo_centavos)
                    ) / 100.0 AS lucro_estimado
                FROM movimentacoes_estoque m
                JOIN produtos p ON p.id = m.produto_id
                WHERE m.tipo = 'SAIDA' AND m.data BETWEEN ? AND ?
                GROUP BY p.id, p.nome, m.tamanho, m.unidade
                ORDER BY total_faturado DESC
            """, (inicio_full, fim_full)).fetchall()

            # 4. ESTOQUE CRÍTICO
            estoque_baixo = conn.execute("""
                SELECT nome, quantidade, estoque_minimo 
                FROM produtos 
                WHERE quantidade <= estoque_minimo AND ativo = 1
                ORDER BY quantidade ASC LIMIT 15
            """).fetchall()

            return {
                "financeiro": dict(financeiro) if financeiro and financeiro["total_vendas"] > 0 else {
                    "total_vendas": 0, "faturamento": 0.0, "ticket_medio": 0.0
                },
                "pagamentos": [
                    {
                        **dict(r),
                        "total": r["total"] / 100
                    }
                    for r in pagamentos
                ],
               "produtos": [
                    {
                        **dict(r),

                        # banco centavos -> tela reais
                        "preco_compra": int(r["custo_centavos"]) / 100,
                        "preco_venda": int(r["preco_centavos"]) / 100,

                        # movimentação já está em reais
                        "total_faturado": float(r["total_faturado"] or 0),

                        "lucro_estimado": float(r["lucro_estimado"] or 0),
                    }
                    for r in produtos
                ],
                "estoque_baixo": [dict(r) for r in estoque_baixo]
            }
    
    @staticmethod
    def obter_relatorio_movimentacoes() -> list[dict]:
        """Retorna os dados usando a função que já funciona na sua interface principal."""
        try:
            from services.produtos_service import listar_movimentacoes
            
            dados = listar_movimentacoes(limite=2000)
            
            formatados = []
            for d in dados:
                formatados.append({
                    "data": d.get("data"),
                    "tipo": d.get("tipo"),
                    "produto": d.get("produto_nome"),
                    "quantidade": d.get("quantidade"),
                    "observacao": d.get("observacao"),
                    "usuario": d.get("usuario_nome")
                })
            return formatados
        except Exception as e:
            print(f"Erro ao carregar dados do service existente: {e}")
            return []