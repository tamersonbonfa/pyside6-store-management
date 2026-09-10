# 🛍️ Desktop Management System

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/PySide-6-41CD52?style=for-the-badge&logo=qt&logoColor=white" alt="PySide6">
  <img src="https://img.shields.io/badge/SQLite-3-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite">
</p>

---

<details>
<summary>🚀 <strong>Funcionalidades Principais</strong></summary>
<br>

| Recurso | Descrição |
| :--- | :--- |
| **📦 Gestão de Inventário** | Cadastro completo de produtos com controle de tamanho, unidade e estoque mínimo. |
| **💳 PDV Otimizado** | Fluxo de caixa ágil com suporte a múltiplas formas de pagamento: PIX, Cartão e Dinheiro. |
| **📊 Dashboard Gerencial** | Relatórios em tempo real com métricas de faturamento, ticket médio e lucro estimado. |
| **📑 Histórico Total** | Rastreabilidade completa de entradas e saídas de estoque com logs detalhados de usuário. |
| **🎨 Interface Premium** | UI moderna em **PySide6** com tema Dark, focada em usabilidade e redução de fadiga visual. |
<br>
<br>
<br>

</details>

<details>
<summary>🛠️ <strong>Stack Tecnológica</strong></summary>
<br>

* **Core:** Python (3.10, 3.11, 3.12)
* **GUI:** PySide6 (Qt for Python) com widgets customizados
* **Database:** SQLite com suporte a transações ACID
* **Arquitetura:** Separação modular entre `services/` e `ui/`
<br>
<br>
<br>

</details>

<details>
<summary>📁 <strong>Estrutura do Projeto</strong></summary>
<br>

```bash
├── 🗄️ database/    # Configurações e inicialização do SQLite (database.db)
├── ⚙️ services/    # Lógica de negócio (Relatórios, Estoque, Vendas)
├── 🖼️ ui/          # Camada de visualização (Main, Relatórios, Login)
├── 🎨 assets/      # Ícones, logotipos e recursos visuais
└── 🚀 main.py      # Ponto de entrada da aplicação

```
<br>
<br>
<br>

</details>

<details>
<summary>⚙️ <strong>Configuração e Instalação</strong></summary>
<br>

1. Clonar o Repositório
```bash

git clone https://github.com/tamersonbonfa/pyside6-store-management.git pyside6-store-management

```
```bash

cd pyside6-store-management

```

2. Baixar e instalar Miniconda pelo link:
```bash

https://www.anaconda.com/download/success

```
3. Configurar ambiente virtual no miniconda:

# Criando ambiente virtual pelo conda:
```bash

conda create -n pyside6-store-management python=3.12

```

# Ativação ambiente pelo conda:
```bash

conda activate pyside6-store-management

```

3. Instalar Dependências:
```bash

pip install -r requirements.txt

```

4. Iniciar sistema:
```bash

python main.py

```

💡 Nota: O sistema inicializa automaticamente o arquivo database/database.db na primeira execução.
<br>
<br>
<br>

</details>

<details>
<summary>🧪 <strong>Ferramentas de Desenvolvimento</strong></summary>
<br>
O projeto inclui o script utilitário injetor.py para testes de estresse:

Simulação Realista: Gera movimentações de estoque e vendas fictícias.

Validação: Ideal para validar o comportamento dos gráficos e relatórios gerenciais.
<br>
<br>
<br>

</details>
<br>
<br>
<br>

<p align="center">
Desenvolvido por <strong>Tamerson Bonfa</strong>
</p>
