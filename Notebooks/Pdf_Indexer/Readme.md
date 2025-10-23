# 📄 PDF Indexer — Indexação e Pré-processamento de PDFs

## 📘 Descrição Geral
O arquivo implementa classes para **pré-processamento e indexação de PDFs** em Pinecone, utilizando LangChain.  
Ele realiza:

- Limpeza e normalização de texto.
- Extração de CPF e CNPJ do contratado.
- Split de documentos em **chunks respeitando parágrafos completos**.
- Indexação em vetor store

---

## ⚙️ Classes e Funcionalidades

### **1️⃣ ParagraphTextSplitter**
> Splitter de texto que respeita parágrafos, evitando cortar cláusulas.

- **Parâmetros:**
  - `chunk_size`: tamanho máximo de cada chunk (padrão: 1000)
  - `chunk_overlap`: sobreposição entre chunks (padrão: 200)
- **Métodos:**
  - `split_text(text: str) -> list[str]`: divide um texto em chunks respeitando parágrafos.
  - `split_documents(documents: list[Document]) -> list[Document]`: divide documentos em chunks, preservando metadados.

**Exemplo de uso:**
```python
splitter = ParagraphTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = splitter.split_text(texto)
```

---

### **2️⃣ PDFIndexer**
> Classe para indexação de PDFs em Pinecone, extraindo metadados e processando chunks.

- **Atributos principais:**
  - `folder`: pasta onde os PDFs estão armazenados
  - `index_name`: nome do índice Pinecone
  - `embeddings`: embeddings OpenAI
  - `vectorstore`: PineconeVectorStore
  - `chunk_size` e `chunk_overlap`: parâmetros de chunk

- **Metadados adicionados em cada chunk:**
  - `cnpj_contratado`: primeira ocorrência de CNPJ na primeira página
  - `cpf_contratado`: primeira ocorrência de CPF na primeira página
  - `contractor`: nome fixo do contratado (`PARQUE CIENTÍFICO E TECNOLÓGICO DE BIOCIÊNCIAS LTDA`)
  - `source_file`: nome do PDF

- **Métodos principais:**
  - `_create_index_if_needed()`: cria o índice Pinecone caso não exista.
  - `_load_pdf(path: str)`: carrega um PDF usando `PyPDFLoader`.
  - `index_pdfs()`: percorre todos os PDFs da pasta, extrai chaves, divide em chunks e envia para Pinecone.

**Exemplo de uso:**
```python
indexer = PDFIndexer()
indexer.index_pdfs()
```

---

## 🧠 Observações

- Utiliza a classe **TextProcessor** (`preprocess.py`) para limpeza de texto e extração de CPF/CNPJ.
- Os chunks respeitam **parágrafos inteiros** e podem ter sobreposição configurável.
- Logs são exibidos para monitorar progresso, erros e metadados extraídos.
- Preparado para **pipelines de RAG** e busca semântica em documentos PDF.

---

## ✅ Status
- Classes implementadas e testadas.
- Indexação de PDFs funcional.
- Integração com Pinecone e LangChain pronta para uso.
