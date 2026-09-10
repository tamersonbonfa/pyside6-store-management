from __future__ import annotations
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QFormLayout, QDialog,
    QSpinBox, QDoubleSpinBox, QCheckBox, QTextEdit, QSplitter, QComboBox
)
from services.produtos_service import (
    listar_produtos,
    buscar_produtos_por_nome,
    criar_produto,
    atualizar_produto,
    registrar_entrada_estoque,
    registrar_ajuste_estoque,
    listar_movimentacoes,
)

from config import (
    CATEGORIAS_PRODUTOS, # IMPORTAR A LISTA DE CATEGORIAS DO CONFIG.PY
    UNIDADE_PRODUTOS
)
import pandas as pd
from datetime import datetime, timedelta
from PySide6.QtWidgets import QFileDialog, QComboBox

# --- FUNÇÕES UTILITÁRIAS ---
def _money(v: float) -> str:
    try:
        return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"

def _format_tamanho(v: float, unidade: str) -> str:
    return f"{int(v)}" if v.is_integer() else f"{v}"

# --- DIALOGS ---
class RelatorioMovimentacoesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Relatório Geral de Movimentações")
        self.resize(1200, 750)
        self.dados_brutos = [] # Dados sem filtro para permitir busca rápida
        self.dados_filtrados = [] # Dados após filtros aplicados
        
        layout = QVBoxLayout(self)
        
        # --- CABEÇALHO DE FILTROS ---
        filtros_container = QVBoxLayout()
        
        # Linha 1: Título e Períodos
        linha1 = QHBoxLayout()
        self.lbl_info = QLabel("📋 Histórico de Movimentações")
        self.lbl_info.setObjectName("Title")
        
        self.periodos_layout = QHBoxLayout()
        self.btn_hoje = QPushButton("Hoje")
        self.btn_semana = QPushButton("Semana")
        self.btn_mes = QPushButton("Mês")
        self.btn_ano = QPushButton("Ano")
        self.btn_geral = QPushButton("Geral")
        
        for btn in [self.btn_hoje, self.btn_semana, self.btn_mes, self.btn_ano, self.btn_geral]:
            self.periodos_layout.addWidget(btn)
            
        linha1.addWidget(self.lbl_info, 1)
        linha1.addLayout(self.periodos_layout)
        filtros_container.addLayout(linha1)

        # Linha 2: Categorias e Usuário
        linha2 = QHBoxLayout()
        
        self.cb_filtro_categoria = QComboBox()
        self.cb_filtro_categoria.addItem("Todas as Categorias")
        self.cb_filtro_categoria.addItems(CATEGORIAS_PRODUTOS)
        
        self.cb_filtro_usuario = QComboBox()
        self.cb_filtro_usuario.addItem("Todos os Usuários")
        
        linha2.addWidget(QLabel("Filtrar por:"))
        linha2.addWidget(self.cb_filtro_categoria, 1)
        linha2.addWidget(self.cb_filtro_usuario, 1)
        linha2.addStretch(2)
        filtros_container.addLayout(linha2)
        
        layout.addLayout(filtros_container)

        # --- TABELA ---
        self.tbl = QTableWidget(0, 12)
        self.tbl.setHorizontalHeaderLabels([
            "Data", "Tipo", "Produto", "Cat.", "Qtd", "Tam", "Un", "Obs", "Venda", "Usuário", "Valor", "Desc"
        ])
        self.tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl.setAlternatingRowColors(True)
        layout.addWidget(self.tbl)

        # --- RODAPÉ ---
        footer = QHBoxLayout()
        self.btn_excel = QPushButton("📗 Exportar para Excel")
        self.btn_excel.setObjectName("Primary")
        self.btn_fechar = QPushButton("Fechar")
        
        footer.addWidget(self.btn_excel)
        footer.addStretch(1)
        footer.addWidget(self.btn_fechar)
        layout.addLayout(footer)

        # --- EVENTOS ---
        self.btn_fechar.clicked.connect(self.accept)
        self.btn_excel.clicked.connect(self.exportar_excel)
        
        self.btn_hoje.clicked.connect(lambda: self.aplicar_filtros(periodo="hoje"))
        self.btn_semana.clicked.connect(lambda: self.aplicar_filtros(periodo="semana"))
        self.btn_mes.clicked.connect(lambda: self.aplicar_filtros(periodo="mes"))
        self.btn_ano.clicked.connect(lambda: self.aplicar_filtros(periodo="ano"))
        self.btn_geral.clicked.connect(lambda: self.aplicar_filtros(periodo="geral"))
        
        self.cb_filtro_categoria.currentTextChanged.connect(lambda: self.aplicar_filtros())
        self.cb_filtro_usuario.currentTextChanged.connect(lambda: self.aplicar_filtros())

        self.carregar_dados_iniciais()

    def carregar_dados_iniciais(self):
        """Carrega os dados do banco uma única vez para o cache"""
        try:
            from services.produtos_service import listar_movimentacoes
            self.dados_brutos = listar_movimentacoes(limite=5000)
            
            # Preencher o Combo de Usuários dinamicamente com quem já fez movimentações
            usuarios = sorted(list(set(str(d.get("usuario_nome") or "Sistema") for d in self.dados_brutos)))
            self.cb_filtro_usuario.clear()
            self.cb_filtro_usuario.addItem("Todos os Usuários")
            self.cb_filtro_usuario.addItems(usuarios)
            
            self.aplicar_filtros("geral")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar dados: {e}")

    def aplicar_filtros(self, periodo=None):
        """Aplica múltiplos filtros simultaneamente (Data + Categoria + Usuário)"""
        # Se não passar período, mantém o que está implícito ou busca do botão (padrão geral)
        # Para simplificar, vamos usar uma variável de controle de período se necessário, 
        # mas aqui aplicaremos os filtros de texto sempre.
        
        categoria_alvo = self.cb_filtro_categoria.currentText()
        usuario_alvo = self.cb_filtro_usuario.currentText()
        
        agora = datetime.now()
        self.dados_filtrados = []

        for d in self.dados_brutos:
            # 1. Filtro de Categoria (Note: sua listar_movimentacoes precisa retornar 'categoria' no dicionário)
            cat_doc = d.get("categoria") or "Outros"
            if categoria_alvo != "Todas as Categorias" and cat_doc != categoria_alvo:
                continue
                
            # 2. Filtro de Usuário
            user_doc = str(d.get("usuario_nome") or "Sistema")
            if usuario_alvo != "Todos os Usuários" and user_doc != usuario_alvo:
                continue
            
            # 3. Filtro de Período (Opcional, se 'periodo' for enviado)
            if periodo:
                try:
                    dt = datetime.strptime(d["data"], "%Y-%m-%d %H:%M:%S")
                    if periodo == "hoje" and dt.date() != agora.date(): continue
                    if periodo == "semana" and dt < agora - timedelta(days=7): continue
                    if periodo == "mes" and dt < agora - timedelta(days=30): continue
                    if periodo == "ano" and dt < agora - timedelta(days=365): continue
                except: pass

            self.dados_filtrados.append(d)

        self._renderizar_tabela(self.dados_filtrados)

    def _renderizar_tabela(self, dados):
        self.tbl.setRowCount(0)
        for m in dados:
            r = self.tbl.rowCount()
            self.tbl.insertRow(r)
            
            tipo = str(m.get("tipo") or "").upper()
            
            # Adicionado m.get("categoria") na lista de itens
            items = [
                str(m.get("data") or ""),
                tipo,
                str(m.get("produto_nome") or ""),
                str(m.get("categoria") or "Outros"),
                str(m.get("quantidade") or 0),
                str(m.get("tamanho") or ""),
                str(m.get("unidade") or ""),
                str(m.get("observacao") or ""),
                str(m.get("venda_id") or ""),
                str(m.get("usuario_nome") or ""),
                _money(float(m.get("valor_venda") or 0)),
                f"{float(m.get('desconto') or 0):.2f}%"
            ]
            
            for c, texto in enumerate(items):
                it = QTableWidgetItem(texto)
                if c in (4, 8): it.setTextAlignment(Qt.AlignCenter) # Ajustado índices por causa da nova coluna
                
                if tipo == "SAIDA": it.setForeground(Qt.red)
                elif tipo == "ENTRADA": it.setForeground(Qt.green)
                elif tipo == "AJUSTE": it.setForeground(Qt.yellow)
                
                self.tbl.setItem(r, c, it)
        self.tbl.resizeColumnsToContents()

    def exportar_excel(self):
        if not self.dados_filtrados:
            QMessageBox.warning(self, "Aviso", "Não há dados para exportar.")
            return

        caminho, _ = QFileDialog.getSaveFileName(
            self, "Salvar Excel", f"Relatorio_Estoque_{datetime.now().strftime('%Y%m%d')}.xlsx", "Excel Files (*.xlsx)"
        )

        if caminho:
                    try:
                        df = pd.DataFrame(self.dados_filtrados)
                        # Incluindo categoria no Excel
                        df = df[['data', 'tipo', 'produto_nome', 'categoria', 'quantidade', 'usuario_nome', 'valor_venda', 'observacao']]
                        df.columns = ['Data', 'Tipo', 'Produto', 'Categoria', 'Qtd', 'Usuário', 'Valor', 'Observação']
                        df.to_excel(caminho, index=False)
                        QMessageBox.information(self, "Sucesso", "Relatório exportado!")
                    except Exception as e:
                        QMessageBox.critical(self, "Erro", f"Falha ao exportar: {e}")

class ProdutoDialog(QDialog):
    def __init__(self, parent=None, produto: dict | None = None):
        super().__init__(parent)
        self.setWindowTitle("Produto")
        self.setMinimumWidth(520)
        self.produto = produto

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(10)

        self.ed_nome = QLineEdit()
        self.ed_marca = QLineEdit()
        self.cb_categoria = QComboBox()
        self.cb_categoria.addItems(CATEGORIAS_PRODUTOS)

        self.sp_tamanho = QDoubleSpinBox()
        self.sp_tamanho.setRange(0, 99999)
        self.sp_tamanho.setDecimals(2)
        self.sp_tamanho.setValue(100)
        self.cb_unidade = QComboBox()
        self.cb_unidade.addItems(UNIDADE_PRODUTOS)

        self.sp_custo = QDoubleSpinBox()
        self.sp_custo.setRange(0, 999999)
        self.sp_custo.setDecimals(2)

        self.sp_preco = QDoubleSpinBox()
        self.sp_preco.setRange(0, 999999)
        self.sp_preco.setDecimals(2)

        self.sp_qtd = QSpinBox()
        self.sp_qtd.setRange(0, 999999)
        self.sp_min = QSpinBox()
        self.sp_min.setRange(0, 999999)

        self.ck_ativo = QCheckBox("Produto ativo")
        self.ck_ativo.setChecked(True)
        self.ed_codigo = QLineEdit()
        self.ed_codigo.setPlaceholderText("Código de barras")

        form.addRow("Nome*", self.ed_nome)
        form.addRow("Marca", self.ed_marca)
        form.addRow("Categoria", self.cb_categoria)
        form.addRow("Tamanho", self.sp_tamanho)
        form.addRow("Unidade", self.cb_unidade)
        form.addRow("Custo (R$)", self.sp_custo)
        form.addRow("Preço venda (R$)", self.sp_preco)
        form.addRow("Quantidade", self.sp_qtd)
        form.addRow("Estoque mínimo", self.sp_min)
        form.addRow("", self.ck_ativo)
        form.addRow("Código de barras", self.ed_codigo)
        layout.addLayout(form)

        row = QHBoxLayout()
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_save = QPushButton("Salvar")
        self.btn_save.setObjectName("Primary")
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_save.clicked.connect(self.accept)
        row.addWidget(self.btn_cancel)
        row.addWidget(self.btn_save)
        layout.addLayout(row)

        if produto:
            self._fill(produto)
            self.sp_qtd.setEnabled(False)

    def _fill(self, p: dict):
        self.ed_nome.setText(str(p.get("nome") or ""))
        self.ed_marca.setText(str(p.get("marca") or ""))
        categoria = p.get("categoria") or "Outros"
        idx = self.cb_categoria.findText(categoria)
        if idx >= 0: self.cb_categoria.setCurrentIndex(idx)
        self.sp_tamanho.setValue(float(p.get("tamanho") or 0))
        unidade = p.get("unidade") or "ml"
        idx = self.cb_unidade.findText(unidade)
        if idx >= 0: self.cb_unidade.setCurrentIndex(idx)
        self.sp_custo.setValue(float(p.get("custo") or 0))
        self.sp_preco.setValue(float(p.get("preco_venda") or 0))
        self.sp_qtd.setValue(int(p.get("quantidade") or 0))
        self.sp_min.setValue(int(p.get("estoque_minimo") or 0))
        self.ck_ativo.setChecked(int(p.get("ativo") or 0) == 1)
        self.ed_codigo.setText(str(p.get("codigo_barras") or ""))

    def get_data(self) -> dict:
        return {
            "nome": self.ed_nome.text().strip(),
            "marca": self.ed_marca.text().strip(),
            "categoria": self.cb_categoria.currentText(),
            "tamanho": float(self.sp_tamanho.value()),
            "unidade": self.cb_unidade.currentText(),
            "custo": float(self.sp_custo.value()),
            "preco_venda": float(self.sp_preco.value()),
            "quantidade": int(self.sp_qtd.value()),
            "estoque_minimo": int(self.sp_min.value()),
            "codigo_barras": self.ed_codigo.text().strip(),
            "ativo": bool(self.ck_ativo.isChecked()),
        }

class EstoqueDialog(QDialog):
    def __init__(self, parent=None, titulo="Movimentação", modo="ENTRADA"):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.setMinimumWidth(520)
        self.modo = modo

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(10)

        self.sp_qtd = QSpinBox()
        self.sp_qtd.setRange(1, 999999)
        self.sp_nova = QSpinBox()
        self.sp_nova.setRange(0, 999999)
        self.ed_obs = QTextEdit()
        self.ed_obs.setFixedHeight(90)

        if modo == "ENTRADA":
            form.addRow("Quantidade (entrada)", self.sp_qtd)
        else:
            form.addRow("Nova quantidade", self.sp_nova)

        form.addRow("Observação", self.ed_obs)
        layout.addLayout(form)

        row = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_ok = QPushButton("Confirmar")
        btn_ok.setObjectName("Primary")
        btn_cancel.clicked.connect(self.reject)
        btn_ok.clicked.connect(self.accept)
        row.addWidget(btn_cancel)
        row.addWidget(btn_ok)
        layout.addLayout(row)

    def get_data(self) -> dict:
        return {
            "quantidade": int(self.sp_qtd.value()),
            "nova_quantidade": int(self.sp_nova.value()),
            "observacao": self.ed_obs.toPlainText().strip(),
        }

# --- TELA PRINCIPAL ---
class TelaProdutos(QWidget):
    def __init__(self, usuario_id: int):
        super().__init__()
        self.usuario_id = usuario_id
        self.produtos_cache: list[dict] = []

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Cabeçalho
        header = QHBoxLayout()
        title = QLabel("📦 Produtos / Estoque")
        title.setObjectName("Title")
        self.ed_busca = QLineEdit()
        self.ed_busca.setPlaceholderText("Buscar...")
        
        self.btn_refresh = QPushButton("🔄 Atualizar")
        self.btn_relatorio_mov = QPushButton("📊 Relatório Mov.") # Novo Botão
        self.btn_novo = QPushButton("➕ Novo Produto")
        self.btn_novo.setObjectName("Primary")

        header.addWidget(title, 1)
        header.addWidget(self.ed_busca, 1)
        header.addWidget(self.btn_refresh)
        header.addWidget(self.btn_relatorio_mov)
        header.addWidget(self.btn_novo)
        layout.addLayout(header)

        splitter = QSplitter(Qt.Vertical)

        # Tabela de produtos
        self.tbl = QTableWidget(0, 12)
        self.tbl.setHorizontalHeaderLabels([
            "ID", "Nome", "Marca", "Categoria", "Tamanho", "Unidade",
            "Custo", "Preço", "Qtd", "Mínimo", "Status", "Barras"
        ])
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)

        actions = QHBoxLayout()
        self.btn_editar = QPushButton("✏️ Editar")
        self.btn_entrada = QPushButton("⬆️ Entrada")
        self.btn_ajuste = QPushButton("🛠️ Ajuste")
        self.btn_mov = QPushButton("📜 Filtrar Histórico")
        actions.addWidget(self.btn_editar)
        actions.addWidget(self.btn_entrada)
        actions.addWidget(self.btn_ajuste)
        actions.addWidget(self.btn_mov)
        actions.addStretch(1)

        top = QWidget()
        top_l = QVBoxLayout(top)
        top_l.setContentsMargins(0, 0, 0, 0)
        top_l.addWidget(self.tbl)
        top_l.addLayout(actions)

        # Rodapé: Histórico Rápido
        self.tbl_mov = QTableWidget(0, 12)
        self.tbl_mov.setHorizontalHeaderLabels([
            "Data", "Tipo", "Produto", "Cat.", "Qtd", "Tam", "Un", "Obs", "Venda", "Usuário", "Valor", "Desc"
        ])
        self.tbl_mov.setEditTriggers(QAbstractItemView.NoEditTriggers)

        bottom = QWidget()
        bottom_l = QVBoxLayout(bottom)
        bottom_l.setContentsMargins(0, 0, 0, 0)
        self.lbl_hist_titulo = QLabel("📜 Histórico Geral (últimas 200)")
        bottom_l.addWidget(self.lbl_hist_titulo)
        bottom_l.addWidget(self.tbl_mov)

        splitter.addWidget(top)
        splitter.addWidget(bottom)
        splitter.setSizes([420, 220])
        layout.addWidget(splitter, 1)

        # Conexões
        self.btn_novo.clicked.connect(self.novo_produto)
        self.btn_refresh.clicked.connect(self.atualizar)
        self.btn_relatorio_mov.clicked.connect(self.abrir_relatorio_geral) # Conexão nova
        self.ed_busca.textChanged.connect(self.buscar)
        self.btn_editar.clicked.connect(self.editar)
        self.btn_entrada.clicked.connect(self.entrada)
        self.btn_ajuste.clicked.connect(self.ajuste)
        self.btn_mov.clicked.connect(self.ver_movimentacoes_selecionado)
        self.tbl.doubleClicked.connect(self.editar)

        self.carregar()
        self.carregar_movimentacoes()

    def abrir_relatorio_geral(self):
        """Abre a nova tela de relatório completo"""
        dlg = RelatorioMovimentacoesDialog(self)
        dlg.exec()

    def _selected_produto(self) -> dict | None:
        row = self.tbl.currentRow()
        if row < 0: return None
        pid_item = self.tbl.item(row, 0)
        if not pid_item: return None
        pid = int(pid_item.text())
        return next((p for p in self.produtos_cache if int(p["id"]) == pid), None)

    def atualizar(self):
        self.carregar()
        self.carregar_movimentacoes(None)

    def carregar(self):
        self.produtos_cache = listar_produtos(apenas_ativos=False)
        self._render_tabela(self.produtos_cache)

    def buscar(self):
        texto = self.ed_busca.text().strip()
        self.produtos_cache = buscar_produtos_por_nome(texto, apenas_ativos=False)
        self._render_tabela(self.produtos_cache)

    def _render_tabela(self, data: list[dict]):
        self.tbl.setRowCount(0)
        for p in data:
            r = self.tbl.rowCount()
            self.tbl.insertRow(r)
            qtd = int(p.get("quantidade") or 0)
            minimo = int(p.get("estoque_minimo") or 0)
            ativo = int(p.get("ativo") or 0) == 1
            status = "ATIVO" if ativo else "INATIVO"
            if ativo and minimo > 0 and qtd <= minimo: status = "⚠️ BAIXO"

            values = [
                str(p["id"]), str(p.get("nome") or ""), str(p.get("marca") or ""),
                str(p.get("categoria") or ""),
                _format_tamanho(float(p.get("tamanho") or 0), p.get("unidade") or "ml"),
                str(p.get("unidade") or ""), _money(float(p.get("custo") or 0)),
                _money(float(p.get("preco_venda") or 0)), str(qtd), str(minimo),
                status, str(p.get("codigo_barras") or "")
            ]
            for c, v in enumerate(values):
                it = QTableWidgetItem(v)
                if c in (0, 4, 7, 8, 9): it.setTextAlignment(Qt.AlignCenter)
                self.tbl.setItem(r, c, it)
        self.tbl.resizeColumnsToContents()

    def novo_produto(self):
        dlg = ProdutoDialog(self)
        if dlg.exec() == QDialog.Accepted:
            criar_produto(**dlg.get_data())
            self.atualizar()

    def editar(self):
        p = self._selected_produto()
        if not p: return
        dlg = ProdutoDialog(self, produto=p)
        if dlg.exec() == QDialog.Accepted:
            dados = dlg.get_data()

            dados.pop("quantidade", None)

            atualizar_produto(
                produto_id=int(p["id"]),
                **dados
            )
            self.carregar()

    def entrada(self):
        p = self._selected_produto()
        if not p: return
        dlg = EstoqueDialog(self, titulo="Entrada", modo="ENTRADA")
        if dlg.exec() == QDialog.Accepted:
            d = dlg.get_data()
            registrar_entrada_estoque(int(p["id"]), int(d["quantidade"]), d["observacao"], self.usuario_id)
            self.atualizar()

    def ajuste(self):
        p = self._selected_produto()
        if not p: return
        dlg = EstoqueDialog(self, titulo="Ajuste", modo="AJUSTE")
        if dlg.exec() == QDialog.Accepted:
            d = dlg.get_data()
            registrar_ajuste_estoque(int(p["id"]), int(d["nova_quantidade"]), d["observacao"], self.usuario_id)
            self.atualizar()

    def ver_movimentacoes_selecionado(self):
        p = self._selected_produto()
        if not p:
            QMessageBox.information(self, "Aviso", "Selecione um produto.")
            return
        self.carregar_movimentacoes(produto_id=int(p["id"]))

    def carregar_movimentacoes(self, produto_id: int | None = None):
        movs = listar_movimentacoes(produto_id=produto_id, limite=200)
        self.lbl_hist_titulo.setText(f"📜 Histórico: {self._selected_produto()['nome'] if produto_id else 'Geral'}")
        self.tbl_mov.setRowCount(0)
        for m in movs:
            r = self.tbl_mov.rowCount()
            self.tbl_mov.insertRow(r)
            values = [
                str(m.get("data") or ""), 
                str(m.get("tipo") or ""), 
                str(m.get("produto_nome") or ""),
                str(m.get("categoria") or "Outros"),
                str(m.get("quantidade") or 0), 
                _format_tamanho(float(m.get("tamanho") or 0), "un"),
                str(m.get("unidade") or ""), 
                str(m.get("observacao") or ""), 
                str(m.get("venda_id") or ""),
                str(m.get("usuario_nome") or ""), 
                _money(float(m.get("valor_venda") or 0)),
                f"{float(m.get('desconto') or 0):.2f}%"
            ]
            for c, v in enumerate(values):
                it = QTableWidgetItem(v)
                self.tbl_mov.setItem(r, c, it)
        self.tbl_mov.resizeColumnsToContents()