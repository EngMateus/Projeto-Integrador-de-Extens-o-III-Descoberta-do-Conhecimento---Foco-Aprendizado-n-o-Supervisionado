import logging
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_openai import OpenAIEmbeddings
from langchain_community.chat_models import ChatOpenAI
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone as PineconeClient
from rapidfuzz import process, fuzz
from src.config.settings import settings

# Imports para Streaming
from langchain.schema.runnable import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser


def normalize_id_key(key: str) -> str:
    """Remove tudo que não é número de um CNPJ ou CPF."""
    return "".join(filter(str.isdigit, key or ""))


class CachedPineconeVectorStore(PineconeVectorStore):
    """
    Extensão de PineconeVectorStore com cache de source_file robusto.
    """

    def __init__(self, index_name: str, embeddings):
        super().__init__(index_name=index_name, embedding=embeddings, text_key="text")
        self._pc = PineconeClient(
            api_key=settings.PINECONE_API_KEY, environment=settings.PINECONE_ENVIRONMENT)
        self._index = self._pc.Index(index_name)
        self._emb = embeddings
        self._source_files_cache: list[str] | None = None

    @property
    def index(self): return self._index
    @property
    def embeddings(self): return self._emb

    def get_all_source_files(self) -> list[str]:
        """Retorna todos os source_file do índice Pinecone (aumentado para 10k)."""
        if self._source_files_cache is not None:
            return self._source_files_cache

        all_files = set()
        # Gera um vetor dummy para consulta de metadados
        empty_vec = self._emb.embed_query(" ")

        try:
            # CORREÇÃO CRÍTICA: Aumentei top_k de 500 para 10000.
            # Isso garante que o sistema veja TODOS os arquivos indexados.
            result = self._index.query(
                vector=empty_vec,
                top_k=10000,
                include_metadata=True,
                filter={}
            )
            matches = result.get("matches", [])
            for m in matches:
                sf = m.get("metadata", {}).get("source_file")
                if sf:
                    all_files.add(sf.strip().lower())
        except Exception as e:
            print(f"Erro ao atualizar cache de arquivos: {e}")

        self._source_files_cache = sorted(all_files)
        return self._source_files_cache


class RAGPipeline:
    def __init__(self, logger: logging.Logger | None = None):
        self.logger = logger or logging.getLogger(__name__)
        self.pc = PineconeClient(
            api_key=settings.PINECONE_API_KEY, environment=settings.PINECONE_ENVIRONMENT)
        self.embeddings = OpenAIEmbeddings(model=settings.EMBEDDING_MODEL)
        self.vectorstore = CachedPineconeVectorStore(
            index_name=settings.PINECONE_INDEX_NAME,
            embeddings=self.embeddings
        )

        self.llm = ChatOpenAI(
            model_name=settings.LLM_MODEL,
            temperature=settings.TEMPERATURE,
            streaming=True,  # Habilita o streaming (efeito digitação)
            api_key=settings.OPENAI_API_KEY
        )

        self.prompt_template = PromptTemplate(
            template="""Você é um assistente jurídico especializado em análise de contratos.
Responda EXCLUSIVAMENTE com base nos trechos abaixo.
Se a resposta não estiver clara no texto ou não existir, diga: "Não encontrei essa informação no documento."

---
CONTEXTO:
{context}
---

PERGUNTA: {question}
---

**Instruções:**
- Responda de forma objetiva e técnica.
- Use apenas informações do contexto.
- Cite cláusulas quando possível.
- Nunca invente informações.
""",
            input_variables=["context", "question"]
        )

    def get_qa_chain(self, question: str, search_key: dict):
        """Prepara a chain para Streaming no Flask."""
        # 1. Resolve Filtros
        final_filter = {}
        if search_key:
            if "cnpj_contratado" in search_key or "cpf_contratado" in search_key:
                final_filter = search_key
            elif "source_file" in search_key:
                fuzzy = self._fuzzy_source_file_filter(
                    search_key["source_file"])
                if fuzzy:
                    final_filter = fuzzy

        # 2. Busca Documentos
        self.logger.info(f"🔍 [RAG] Buscando com filtro: {final_filter}")
        docs = self.vectorstore.similarity_search(
            question, k=6, filter=final_filter)

        # Log para debug
        if not docs:
            self.logger.warning(
                "⚠️ ZERO documentos retornados do Pinecone. Verifique o filtro.")
            context_str = "Nenhum documento encontrado."
        else:
            self.logger.info(
                f"✅ {len(docs)} documentos recuperados para contexto.")
            context_str = "\n\n".join([d.page_content for d in docs])

        # 3. Monta a Chain
        chain = (
            {"context": lambda x: context_str,
                "question": lambda x: x["query"]}
            | self.prompt_template
            | self.llm
            | StrOutputParser()
        )
        return chain

    # Fallback para filtro fuzzy (nome do arquivo)
    def _fuzzy_source_file_filter(self, input_name: str) -> dict | None:
        if not input_name:
            return None

        # Limpeza idêntica ao indexador (troca ponto por espaço)
        input_name_clean = input_name.strip().lower().replace(".pdf", "").replace(".", " ")

        all_files = self.vectorstore.get_all_source_files()

        # Se cache vazio, retorna filtro exato direto
        if not all_files:
            return {"source_file": {"$eq": input_name_clean}}

        # Match fuzzy (encontra o nome mais parecido na lista)
        result = process.extractOne(
            input_name_clean, all_files, scorer=fuzz.token_sort_ratio)
        best_match, score = (result[0], result[1]) if result else (None, 0)

        if best_match and score > 65:
            self.logger.info(
                f"🎯 Fuzzy Match: '{input_name}' -> '{best_match}' ({score}%)")
            return {"source_file": {"$eq": best_match}}
        else:
            self.logger.warning(
                f"⚠️ Fuzzy falhou para '{input_name}'. Usando exato: '{input_name_clean}'")
            return {"source_file": {"$eq": input_name_clean}}
