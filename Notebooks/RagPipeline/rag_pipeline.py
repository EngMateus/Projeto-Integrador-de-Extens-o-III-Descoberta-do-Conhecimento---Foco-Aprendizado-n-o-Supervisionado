import logging
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_openai import OpenAIEmbeddings
from langchain_community.chat_models import ChatOpenAI
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone as PineconeClient
from src.core.preprocess import TextProcessor
from src.config.settings import settings


class RAGPipeline:
    """
    Classe que encapsula o retriever + LLM e fornece método de resposta.
    Permite busca por CPF ou CNPJ usando os metadados 'cpf_contratado' e 'cnpj_contratado'.
    """

    def __init__(self, logger: logging.Logger | None = None):
        self.logger = logger or logging.getLogger(__name__)
        self.pinecone = PineconeClient(
            api_key=settings.PINECONE_API_KEY,
            environment=settings.PINECONE_ENVIRONMENT
        )
        self.embeddings = OpenAIEmbeddings(model=settings.EMBEDDING_MODEL)
        self.vectorstore = PineconeVectorStore(
            index_name=settings.PINECONE_INDEX_NAME,
            embedding=self.embeddings,
            text_key="text"
        )
        self.llm = ChatOpenAI(model_name=settings.LLM_MODEL, temperature=settings.TEMPERATURE)
        self.prompt_template = PromptTemplate(
        template="""
        Você é um **Analista de Conformidade (Compliance) Extremo e Jurídico**. Sua missão é responder a perguntas complexas do usuário de forma **ABSURDAMENTE RIGOROSA, EXATA e com fidelidade ABSOLUTA ao texto do Contrato de Associação (Contexto)**.

        **IDENTIFICAÇÃO DE PARTES (VERIFICAÇÃO IMPERATIVA):**
        * **EMPRESA ASSOCIADA (AD FOODS INDÚSTRIA...):** CNPJ 10.767.821/0001-01. Sócio: Eduardo de Souza Pessôa. E-mail Notificação: processos3@adfoods.com.br.
        * **BIOPARK (PARQUE CIENTÍFICO...):** CNPJ 21.526.709/0001-03. Representante: Paulo Victor Almeida. E-mail Notificação: institucional@biopark.com.br.
    
        **ANTES DE RESPONDER, verifique sempre se os dados (CNPJ, CPF, Endereço, E-mail) referem-se à PARTE correta. A inversão de dados é uma falha inaceitável.**

        **REGRAS DE RIGOR E FIDELIDADE (CUMPRIMENTO OBRIGATÓRIO):**
        1.  **Fidelidade Estrita:** Se a informação estiver presente, extraia e forneça a resposta **exata e concisa**, incluindo referências (Artigo, §, Cláusula) se mencionadas.
        2.  **Exaustão de Listas:** Quando a pergunta for sobre listas, enumerações, ou múltiplas condições, você deve listar **todos** os itens ou condições encontrados no contexto.
        3.  **Rigor Lógico e Cálculo (Verificação Imperativa):** Se a pergunta se refere a uma penalidade (ex: multa por rescisão), você DEVE primeiro identificar o prazo e a condição estabelecida.
        * **CÁLCULO DE PRAZO:** A data de início é **01 de agosto de 2023**. O prazo de 6 meses para multa vai até **01 de fevereiro de 2024**.
        * **APLICAÇÃO:** A penalidade SÓ SE APLICA se a condição for ATENDIDA EXATAMENTE. Se a data da pergunta for **APÓS** a data de corte (01 de fev. 2024), a penalidade **NÃO SE APLICA (ZERO)**. Sua resposta deve explicar a razão.
        4.  **Análise Lógica (Inferência de Negação):** Se a pergunta questionar sobre uma garantia, permissão ou prevalência que é explicitamente limitada (ou negada) pelo texto, sua resposta deve inferir a negação/limitação a partir do texto.
        5.  **Atenção a Exclusões (Aléms/Excetos):** Se a pergunta solicitar uma lista de itens "além de X" ou "exceto Y", você **não deve incluir** X ou Y na sua lista final.
        6.  **Resposta Negativa Rigorosa:** Use a resposta: "Não encontrei essa informação no(s) documento(s) fornecido(s)." APENAS se a informação for IRRECUPERÁVEL (não há menção ou base para inferência). **NUNCA use esta resposta se a informação puder ser extraída da seção 'IDENTIFICAÇÃO DE PARTES' ou da lógica do contrato (Regra 3).**

        Contexto:
        {context}

        Pergunta:
        {question}
        """,
        input_variables=["context", "question"]
        )

    def answer(self, search_key: str, question: str, k: int = 30) -> dict: # estava com top k = 4
        """
        Retorna um dicionário: {'answer': str, 'context': List[str]}
        A busca será feita nos metadados 'cpf_contratado' e 'cnpj_contratado'.
        """
        normalized_key = TextProcessor.normalize_key(search_key)
        self.logger.info(f"🔍 Buscando por CPF/CNPJ: {normalized_key}")

        # Recuperador com filtro em ambos os metadados
        retriever = self.vectorstore.as_retriever(
            search_kwargs={
                "filter": {
                    "$or": [
                        {"cnpj_contratado": {"$eq": normalized_key}},
                        {"cpf_contratado": {"$eq": normalized_key}}
                    ]
                },
                "k": k
            }
        )

        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",  
            retriever=retriever,
            chain_type_kwargs={"prompt": self.prompt_template}
        )

        try:
            docs = retriever.get_relevant_documents(question)
            context_snippets = [d.page_content for d in docs]
            
            
            for i, d in enumerate(docs):
                self.logger.info(f"📄 Chunk {i+1}:")
                self.logger.info(f"Conteúdo: {d.page_content}")
                self.logger.info(f"Metadados: {d.metadata}")
            
            if not context_snippets:
                self.logger.warning("Nenhum contexto encontrado para este CPF/CNPJ.")
                return {"answer": "Nenhuma informação encontrada para este CPF/CNPJ.", "context": []}
            
            combined_context = "\n\n".join(context_snippets)
            self.logger.info("🧩 Contexto passado para a LLM:\n" + combined_context)  # mostra só os primeiros 2000 chars

            self.logger.info(f"❓ Pergunta: {question}")

            answer = qa_chain.run(question)
            self.logger.info("Resposta gerada com sucesso.")
            return {"answer": answer, "context": context_snippets}
        except Exception as e:
            self.logger.exception("Erro ao gerar resposta:")
            return {"answer": f"Erro ao gerar resposta: {e}", "context": []}
