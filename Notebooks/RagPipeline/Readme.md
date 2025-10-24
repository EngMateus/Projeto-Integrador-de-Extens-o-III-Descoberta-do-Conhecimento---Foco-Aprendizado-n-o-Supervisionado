# 🤖 RAGPipeline — Busca e Resposta Baseada em PDFs

## 📘 Descrição Geral
O arquivo implementa a classe **`RAGPipeline`**, que encapsula o **retriever + LLM** para fornecer respostas **precisas e contextualizadas** a perguntas sobre documentos PDF indexados.  
Ele permite **busca por CPF ou CNPJ**, utilizando metadados dos documentos (`cpf_contratado`, `cnpj_contratado`), garantindo respostas **rigorosas e confiáveis**.


Autor: Kevin

---

## ⚙️ Classe `RAGPipeline`

### 🔹 Propósito
- Conectar **vectorstore Pinecone** ao modelo de linguagem (LLM) da OpenAI.
- Permitir consultas **semânticas e filtradas por CPF/CNPJ**.
- Fornecer respostas **fidelidade absoluta ao texto do contrato**.

### 🔹 Atributos Principais
- `pinecone`: cliente Pinecone para acesso ao vectorstore.
- `embeddings`: embeddings OpenAI para vetorização do texto.
- `vectorstore`: PineconeVectorStore contendo os chunks indexados.
- `llm`: modelo ChatOpenAI para geração de respostas.
- `prompt_template`: prompt rigoroso com regras de fidelidade, cálculo de prazos e análise lógica.

---

### 🔹 Método `answer(search_key: str, question: str, k: int = 20) -> dict`
- **Função:** retorna um dicionário com a resposta da LLM e os trechos do contexto utilizados.
- **Parâmetros:**
  - `search_key`: CPF ou CNPJ para filtrar documentos.
  - `question`: pergunta do usuário.
  - `k`: número de chunks relevantes a considerar (default: 20).
- **Retorno:**
```python
{
    "answer": "Resposta gerada pela LLM",
    "context": [ "chunk1", "chunk2", ... ]
}
```

- **Processo Interno:**
  1. Normaliza a chave (CPF/CNPJ) usando `TextProcessor`.
  2. Cria um retriever filtrando por `cpf_contratado` e `cnpj_contratado`.
  3. Recupera os documentos relevantes (`k` chunks).
  4. Gera resposta via LLM usando **prompt rigoroso**.
  5. Retorna a resposta e os snippets de contexto.

---

### 🔹 Prompt Template
O prompt define regras de **rigor absoluto**:

- Fidelidade estrita às informações do contrato.
- Exaustão de listas e condições.
- Cálculo de prazos de penalidades.
- Inferência de negação quando aplicável.
- Respostas negativas apenas quando não há base no documento.

---

### 🔹 Observações
- Logs detalhados registram:
  - Chunks recuperados
  - Metadados de cada chunk
  - Contexto enviado à LLM
  - Pergunta e resposta gerada


---

## ✅ Status
- Classe `RAGPipeline` implementada.
- Busca semântica filtrada por CPF/CNPJ funcional.
- Respostas geradas com alta fidelidade ao texto dos PDFs.
