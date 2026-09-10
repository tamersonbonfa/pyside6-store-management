PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    nome TEXT NOT NULL,
    cargo TEXT NOT NULL,
    senha_hash TEXT NOT NULL,
    is_admin INTEGER NOT NULL DEFAULT 0,
    ativo INTEGER NOT NULL DEFAULT 1,
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ultimo_login TEXT
);

CREATE TABLE IF NOT EXISTS configuracoes (
    chave TEXT PRIMARY KEY,
    valor TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    telefone TEXT,
    endereco TEXT,
    observacoes TEXT,
    ativo INTEGER NOT NULL DEFAULT 1,
    criado_em TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    marca TEXT,
    volume_ml INTEGER,
    custo_centavos INTEGER NOT NULL DEFAULT 0,
    preco_centavos INTEGER NOT NULL DEFAULT 0,
    quantidade INTEGER NOT NULL DEFAULT 0,
    estoque_minimo INTEGER NOT NULL DEFAULT 0,
    ativo INTEGER NOT NULL DEFAULT 1,
    criado_em TEXT NOT NULL,
    categoria TEXT DEFAULT 'Outro',
    tamanho REAL DEFAULT 0,
    unidade TEXT DEFAULT 'ml',
    codigo_barras TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS vendas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT NOT NULL,
    cliente_id INTEGER,
    usuario_id INTEGER,
    forma_pagamento TEXT NOT NULL, -- DINHEIRO | PIX | CARTAO
    total_centavos INTEGER NOT NULL,
    valor_pago_centavos INTEGER NOT NULL,
    troco_centavos INTEGER NOT NULL,
    observacoes TEXT,
    FOREIGN KEY(cliente_id) REFERENCES clientes(id) ON DELETE SET NULL,
    FOREIGN KEY(usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS venda_itens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    venda_id INTEGER NOT NULL,
    produto_id INTEGER NOT NULL,
    quantidade INTEGER NOT NULL,
    preco_unitario_centavos INTEGER NOT NULL,
    desconto_centavos INTEGER DEFAULT 0,
    subtotal_centavos INTEGER NOT NULL,
    tamanho REAL,
    unidade TEXT,
    FOREIGN KEY(venda_id) REFERENCES vendas(id) ON DELETE CASCADE,
    FOREIGN KEY(produto_id) REFERENCES produtos(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS movimentacoes_estoque (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT NOT NULL,
    tipo TEXT NOT NULL, -- ENTRADA | SAIDA | AJUSTE
    produto_id INTEGER NOT NULL,
    quantidade INTEGER NOT NULL,
    observacao TEXT,
    usuario_id INTEGER,
    usuario_nome TEXT DEFAULT 'Desconhecido',
    venda_id INTEGER,
    valor_venda INTEGER DEFAULT 0,
    desconto INTEGER DEFAULT 0,
    tamanho REAL DEFAULT 0,
    unidade TEXT DEFAULT 'un',
    FOREIGN KEY(produto_id) REFERENCES produtos(id) ON DELETE RESTRICT,
    FOREIGN KEY(usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL,
    FOREIGN KEY(venda_id) REFERENCES vendas(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_produtos_nome ON produtos(nome);
CREATE INDEX IF NOT EXISTS idx_clientes_nome ON clientes(nome);
CREATE INDEX IF NOT EXISTS idx_vendas_usuario ON vendas(usuario_id);
CREATE INDEX IF NOT EXISTS idx_vendas_data ON vendas(data);
CREATE INDEX IF NOT EXISTS idx_mov_estoque_data ON movimentacoes_estoque(data);
CREATE INDEX IF NOT EXISTS idx_mov_usuario ON movimentacoes_estoque(usuario_id);
CREATE INDEX IF NOT EXISTS idx_produtos_codigo_barras ON produtos(codigo_barras);
