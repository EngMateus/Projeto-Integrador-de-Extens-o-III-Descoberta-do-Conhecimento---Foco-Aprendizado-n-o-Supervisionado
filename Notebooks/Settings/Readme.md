# ⚙️ Configurações Globais — `settings.py`

## 📘 Descrição Geral
O arquivo **`settings.py`** centraliza todas as **configurações globais** do sistema RAG, tornando-as facilmente acessíveis para qualquer módulo do projeto.

Ele carrega parâmetros essenciais, como:

1. Chaves de API (OpenAI, Pinecone)
2. Modelos de LLM
3. Configurações de embeddings
4. Parâmetros de chunking
5. Caminhos de arquivos (PDFs)

Uma instância global da classe `Settings` é criada para garantir acesso unificado.

Autores: Kevin e Mateus

---

## ⚙️ Classe `Settings`

### 🔑 API e Modelos
- `OPENAI_API_KEY`: chave de API da OpenAI
- `LLM_MODEL`: modelo de LLM a ser usado (padrão: `"gpt-3.5-turbo"`)
- `TEMPERATURE`: parâmetro de temperatura do LLM (padrão: `0.2`)
- `PINECONE_API_KEY`: chave de API Pinecone
- `PINECONE_ENVIRONMENT`: ambiente Pinecone
- `PINECONE_INDEX_NAME`: nome do índice Pinecone
- `EMBEDDING_MODEL`: modelo de embedding da OpenAI

---

### 📁 Caminhos de Arquivos
- `PDF_FOLDER`: caminho da pasta onde os PDFs a serem indexados estão localizados (padrão: `"./Documentos"`)

---

### 📝 Parâmetros de Chunking
- `CHUNK_SIZE`: tamanho máximo de cada chunk de texto (padrão: `750`)
- `CHUNK_OVERLAP`: tamanho da sobreposição entre chunks adjacentes (padrão: `150`)

> Esses parâmetros são essenciais para preservar o contexto ao dividir textos longos em pedaços menores.

---

## 🌐 Instância Global
- `settings = Settings()`
- Permite que as configurações sejam importadas e utilizadas em qualquer módulo do projeto sem precisar criar novas instâncias.

---

## ✅ Status
- Arquivo `settings.py` criado e documentado.
- Configurações globais centralizadas e prontas para uso em toda a aplicação.
