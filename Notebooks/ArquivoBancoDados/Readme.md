Arquivo db.py - Configuração e Inicialização
Propósito: Módulo central responsável pela configuração e inicialização do ORM no contexto do Flask.

Instância do ORM:

Cria o objeto principal que fará o mapeamento objeto-relacional: db = SQLAlchemy().

Função init_db(app):

Define o URI de conexão para o banco SQLite: sqlite:///advogados.db.

Conecta o objeto db à instância do aplicativo Flask.

Cria todas as tabelas (modelos) no banco de dados, se não existirem: db.create_all().



Arquivo models.py - Definição do Modelo Advogado
Propósito: Define a estrutura da tabela Advogado, utilizada para armazenar as credenciais de acesso dos usuários.

Estrutura da Tabela Advogado:
Modelo: Herda de db.Model, mapeando a tabela de Advogados.

Campos:

id: Chave primária.

oab_cpf: Coluna de identificação (OAB/CPF). É única e obrigatória (unique=True, nullable=False). Serve como a chave de login.

senha: Coluna obrigatória (nullable=False) para armazenar a senha (deve ser hashed).
