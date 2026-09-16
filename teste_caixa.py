from services.caixa_service import (
    registrar_movimento_caixa,
    saldo_caixa,
    listar_movimentacoes_caixa
)


registrar_movimento_caixa(
    tipo="ABERTURA",
    valor_centavos=10000,
    usuario_id=1,
    descricao="Abertura do caixa"
)


print(
    listar_movimentacoes_caixa()
)


print(
    "Saldo:",
    saldo_caixa()
)