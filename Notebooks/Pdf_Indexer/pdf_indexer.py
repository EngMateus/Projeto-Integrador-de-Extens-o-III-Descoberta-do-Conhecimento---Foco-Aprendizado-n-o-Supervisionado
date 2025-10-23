import os
import logging
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone as PineconeClient, ServerlessSpec
from src.config.settings import settings
from src.core.preprocess import TextProcessor
import re
import warnings
from langchain.schema import Document
warnings.filterwarnings("ignore", category=DeprecationWarning)


class ParagraphTextSplitter:
    """
    Splitter de texto que respeita parágrafos completos, evitando cortar cláusulas.
    """

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(self, text: str) -> list[str]:
        """
        Divide o texto em chunks respeitando parágrafos completos.
        """
        # -> separa por linhas em branco
        paragraphs = re.split(r'\n\s*\n', text)  
        chunks = []
        current_chunk = ""

        for para in paragraphs:
            para = TextProcessor.clean_text(para)
            if not para:
                continue

            if len(current_chunk) + len(para) + 1 > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para
            else:
                current_chunk += " " + para

        if current_chunk:
            chunks.append(current_chunk.strip())

        # -> aplica overlap
        if self.chunk_overlap > 0 and len(chunks) > 1:
            overlapped_chunks = []
            for i in range(len(chunks)):
                chunk = chunks[i]
                if i > 0:
                    prev_chunk = chunks[i - 1]
                    overlap_text = prev_chunk[-self.chunk_overlap:] if self.chunk_overlap < len(prev_chunk) else prev_chunk
                    chunk = overlap_text + " " + chunk
                overlapped_chunks.append(chunk.strip())
            return overlapped_chunks

        return chunks

    def split_documents(self, documents: list[Document]) -> list[Document]:
        """
        Converte cada documento em vários chunks respeitando parágrafos.
        """
        all_chunks = []
        for doc in documents:
            text_chunks = self.split_text(doc.page_content)
            for chunk in text_chunks:
                new_doc = Document(page_content=chunk, metadata=doc.metadata.copy())
                all_chunks.append(new_doc)
        return all_chunks


class PDFIndexer:
    """
    Classe para indexar PDFs no Pinecone.
    cnpj_contratado = primeira ocorrência de CNPJ na primeira página
    cpf_contratado = primeira ocorrência de CPF na primeira página
    contractor = sempre a faculdade
    """

    CONTRACTOR_NAME = "PARQUE CIENTÍFICO E TECNOLÓGICO DE BIOCIÊNCIAS LTDA"

    def __init__(self, logger: logging.Logger | None = None):
        self.logger = logger or logging.getLogger(__name__)
        self.folder = settings.PDF_FOLDER
        self.index_name = settings.PINECONE_INDEX_NAME
        self.embeddings = OpenAIEmbeddings(model=settings.EMBEDDING_MODEL)
        self.pinecone = PineconeClient(
            api_key=settings.PINECONE_API_KEY,
            environment=settings.PINECONE_ENVIRONMENT
        )
        self.vectorstore = PineconeVectorStore(
            index_name=self.index_name,
            embedding=self.embeddings,
            text_key="text",
            namespace=""
        )
        self.chunk_size = settings.CHUNK_SIZE
        self.chunk_overlap = settings.CHUNK_OVERLAP

    def _create_index_if_needed(self):
        try:
            existing = self.pinecone.list_indexes().names()
        except Exception:
            existing = []
        if self.index_name not in existing:
            self.logger.info(f"Criando índice Pinecone: {self.index_name}")
            self.pinecone.create_index(
                name=self.index_name,
                dimension=3072,
                metric="cosine",
                spec=ServerlessSpec(cloud='aws', region='us-east-1')
            )

    def _load_pdf(self, path: str):
        loader = PyPDFLoader(path)
        return loader.load()

    def index_pdfs(self) -> None:
        """
        Indexa todos os PDFs da pasta configurada
        """
        self._create_index_if_needed()

        if not os.path.isdir(self.folder):
            self.logger.warning(f"Pasta de PDFs não encontrada: {self.folder}")
            return

        pdf_files = [f for f in os.listdir(self.folder) if f.lower().endswith(".pdf")]
        if not pdf_files:
            self.logger.info("Nenhum PDF encontrado para indexar.")
            return

        for pdf_file in pdf_files:
            path = os.path.join(self.folder, pdf_file)
            self.logger.info(f"Processando: {pdf_file}")

            try:
                documents = self._load_pdf(path)
            except Exception as e:
                self.logger.exception(f"Falha ao carregar PDF {pdf_file}: {e}")
                continue

            if not documents:
                self.logger.warning(f"PDF {pdf_file} vazio ou não carregado.")
                continue

            # -> Primeira página: extrai CPF e CNPJ do contratado
            first_page_text = documents[0].page_content
            keys = TextProcessor.extract_contractor_keys(first_page_text)

            cnpj_contratado = keys["cnpj_contratado"]
            cpf_contratado = keys["cpf_contratado"]

            self.logger.info(f"CNPJ contratado: {cnpj_contratado}")
            self.logger.info(f"CPF contratado: {cpf_contratado}")
            self.logger.info(f"Contractor (faculdade): {self.CONTRACTOR_NAME}")

            # -> Split em chunks de todo o documento usando ParagraphTextSplitter
            text_splitter = ParagraphTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )
            docs_split = text_splitter.split_documents(documents)

            # -> Adiciona metadados em todos os chunks
            for doc in docs_split:
                doc.metadata["cnpj_contratado"] = cnpj_contratado
                doc.metadata["cpf_contratado"] = cpf_contratado
                doc.metadata["contractor"] = self.CONTRACTOR_NAME
                doc.metadata["source_file"] = pdf_file

            # -> Adiciona ao vectorstore
            try:
                self.vectorstore.add_documents(docs_split)
                self.logger.info(f"{len(docs_split)} chunks indexados do arquivo {pdf_file}")
            except Exception as e:
                self.logger.exception(f"Erro ao enviar chunks para vectorstore: {e}")

        self.logger.info("Indexação concluída.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    indexer = PDFIndexer()
    indexer.index_pdfs()
