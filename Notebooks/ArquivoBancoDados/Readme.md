# 🗂️ Arquivos Implementados

## db.py - Configuração e Inicialização
- **Propósito:** Módulo central responsável pela configuração e inicialização do ORM no contexto do Flask.  
- **Principais pontos:**
  - Criação da instância principal do ORM:  
    ```python
    db = SQLAlchemy()
    ```
  - **Função `init_db(app)`:**
    - Define o URI de conexão com o banco SQLite: `sqlite:///advogados.db`
    - Conecta o objeto `db` à instância do aplicativo Flask
    - Cria todas as tabelas no banco, caso não existam, com `db.create_all()`

---

## models.py - Definição do Modelo Advogado
- **Propósito:** Define a estrutura da tabela `Advogado`, utilizada para armazenar as credenciais de acesso dos usuários.  
- **Estrutura do modelo:**
  - Herda de `db.Model`, mapeando a tabela de `advogados`
  - **Campos:**
    - `id`: Chave primária  
    - `oab_cpf`: Coluna de identificação (OAB/CPF), única e obrigatória (`unique=True, nullable=False`) — usada como chave de login  
    - `senha`: Coluna obrigatória (`nullable=False`) para armazenar a senha (em formato *hash*)
