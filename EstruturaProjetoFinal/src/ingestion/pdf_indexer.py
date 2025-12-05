import os
import logging
import re
import warnings
import hashlib
from pathlib import Path

# --- IMPORTS ---
from llama_parse import LlamaParse 
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone as PineconeClient, ServerlessSpec
from langchain_core.documents import Document

from src.config.settings import settings
from src.core.preprocess import TextProcessor

warnings.filterwarnings("ignore", category=DeprecationWarning)

# --- CLASSE SPLITTER ---
class ParagraphTextSplitter:
    """
    Splitter de texto que respeita parágrafos completos.
    """
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(self, text: str) -> list[str]:
        paragraphs = re.split(r'\n\s*\n', text)  
        chunks = []
        current_chunk = ""

        for para in paragraphs:
            para = TextProcessor.clean_text(para)
            if not para: continue

            if len(current_chunk) + len(para) + 1 > self.chunk_size:
                if current_chunk: chunks.append(current_chunk.strip())
                current_chunk = para
            else:
                current_chunk += " " + para

        if current_chunk: chunks.append(current_chunk.strip())

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
        all_chunks = []
        for doc in documents:
            text_chunks = self.split_text(doc.page_content)
            for chunk in text_chunks:
                new_doc = Document(page_content=chunk, metadata=doc.metadata.copy())
                all_chunks.append(new_doc)
        return all_chunks


# --- CLASSE INDEXER ---
class PDFIndexer:
    """
    Classe para indexar PDFs no Pinecone.
    Versão Otimizada: OCR + Verificação de Duplicidade + IDs Únicos.
    """

    CONTRACTOR_NAME = "PARQUE CIENTÍFICO E TECNOLÓGICO DE BIOCIÊNCIAS LTDA"

    def __init__(self, logger: logging.Logger | None = None):
        self.logger = logger or logging.getLogger(__name__)

        # Configuração da chave do LlamaParse
        if hasattr(settings, "LLAMA_CLOUD_API_KEY") and settings.LLAMA_CLOUD_API_KEY:
            os.environ["LLAMA_CLOUD_API_KEY"] = settings.LLAMA_CLOUD_API_KEY
        else:
            self.logger.warning("LLAMA_CLOUD_API_KEY não encontrada. OCR pode falhar.")

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

    def _is_file_indexed(self, filename_clean: str) -> bool:
        """
        Verifica se já existem vetores no Pinecone com este nome de arquivo.
        """
        try:
            index = self.pinecone.Index(self.index_name)
            query_response = index.query(
                vector=[0.0] * 3072, 
                top_k=1,
                filter={"source_file": {"$eq": filename_clean}},
                include_metadata=False
            )
            return len(query_response['matches']) > 0
        except Exception as e:
            self.logger.error(f"Erro ao verificar arquivo {filename_clean}: {e}")
            return False

    def _load_pdf(self, path: str) -> list[Document]:
        file_name = os.path.basename(path)
        
        # 1. Tentativa Local
        try:
            loader = PyPDFLoader(path)
            documents = loader.load()
            total_text = "".join([doc.page_content for doc in documents])
            if len(total_text.strip()) > 100:
                self.logger.info(f"[{file_name}] PDF Digital detectado. Leitura local.")
                return documents
            self.logger.warning(f"[{file_name}] Texto insuficiente. Possível scan.")
        except Exception as e:
            self.logger.warning(f"[{file_name}] Erro local: {e}. Tentando OCR...")

        # 2. Tentativa LlamaParse
        self.logger.info(f"[{file_name}] Iniciando LlamaParse (OCR)...")
        try:
            parser = LlamaParse(result_type="markdown", language="pt", verbose=True)
            llama_docs = parser.load_data(path)
            if not llama_docs: return []

            full_text = "\n\n".join([doc.text for doc in llama_docs])
            merged_doc = Document(
                page_content=full_text,
                metadata={"source": path, "page": 0, "extraction_method": "llama_parse_ocr"}
            )
            return [merged_doc]
        except Exception as e:
            self.logger.error(f"[{file_name}] Falha no LlamaParse: {e}")
            return []

    def index_pdfs(self) -> None:
        self._create_index_if_needed()

        if not os.path.isdir(self.folder):
            self.logger.warning(f"Pasta não encontrada: {self.folder}")
            return

        pdf_files = [f for f in os.listdir(self.folder) if f.lower().endswith(".pdf")]
        if not pdf_files:
            self.logger.info("Nenhum PDF encontrado.")
            return

        self.logger.info(f"Analisando {len(pdf_files)} arquivos na pasta...")

        for pdf_file in pdf_files:
            path = os.path.join(self.folder, pdf_file)
            
            # 1. Prepara nome limpo
            nome_bruto = Path(pdf_file).stem.lower().replace('.', ' ')
            if len(nome_bruto) > 50:
                nome_limpo = nome_bruto[:-32]
            else:
                nome_limpo = nome_bruto

            # 2. Verifica se pula
            if self._is_file_indexed(nome_limpo):
                self.logger.info(f"⏭️ [PULANDO] Já indexado: {nome_limpo}")
                continue 

            self.logger.info(f"🚀 Indexando NOVO arquivo: {pdf_file}")

            # 3. Carrega
            documents = self._load_pdf(path)
            if not documents: continue

            # Chaves
            first_page_text = documents[0].page_content
            keys = TextProcessor.extract_contractor_keys(first_page_text)
            cnpj_contratado = keys["cnpj_contratado"]
            cpf_contratado = keys["cpf_contratado"]

            # Split
            text_splitter = ParagraphTextSplitter(
                chunk_size=self.chunk_size, 
                chunk_overlap=self.chunk_overlap
            )
            docs_split = text_splitter.split_documents(documents)

            # 4. IDs e Metadados
            ids_para_salvar = []
            for i, doc in enumerate(docs_split):
                doc.metadata["cnpj_contratado"] = cnpj_contratado
                doc.metadata["cpf_contratado"] = cpf_contratado
                doc.metadata["contractor"] = self.CONTRACTOR_NAME
                doc.metadata["source_file"] = nome_limpo
                
                cabecalho_rico = (
                    f"Documento referente a: {nome_limpo}. "
                    f"Contratado CNPJ: {cnpj_contratado}. "
                    f"Contratado CPF: {cpf_contratado}. "
                    f"Conteúdo: "
                )
                doc.page_content = cabecalho_rico + doc.page_content

                # ID Único
                raw_id = f"{pdf_file}_{i}"
                unique_id = hashlib.md5(raw_id.encode()).hexdigest()
                ids_para_salvar.append(unique_id)

            # 5. Salva
            try:
                self.vectorstore.add_documents(docs_split, ids=ids_para_salvar)
                self.logger.info(f"   ✅ Sucesso! {len(docs_split)} vetores salvos.")
            except Exception as e:
                self.logger.exception(f"   ❌ Erro ao salvar vetores: {e}")

        self.logger.info("Ciclo de indexação finalizado.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    indexer = PDFIndexer()
    indexer.index_pdfs()