"""

Armazena as Configurações Globais: 
É a classe central que carrega todos os parâmetros necessários para o funcionamento do sistema RAG, como:

1) Chaves de API
2) Modelos de LLM
3) Configurações de chunking

"""




from dotenv import load_dotenv
from pathlib import Path
import os


load_dotenv()

class Settings:
    
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
    TEMPERATURE = float(os.getenv("TEMPERATURE", 0.2))

    
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
    PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

    """
    Modelo de Embedding: 
    Define o modelo da OpenAI usado para transformar o texto em vetores numéricos (embeddings)
    """
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")


    """
    Caminho dos Arquivos: Define o caminho da pasta onde os PDFs que serão indexados estão localizados
    """
    PDF_FOLDER = Path(os.getenv("PDF_FOLDER", "./Documentos"))
    
    """
    Parâmetros de Chunking:
    Controla o tamanho máximo de cada pedaço de texto (chunk) e o tamanho da sobreposição entre chunks adjacentes, crucial para manter o contexto.
    """
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 750)) # esta em 1500
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 150)) # estava em 200
    





"""
Instância Global:
Cria uma instância única da classe Settings para que as configurações possam ser importadas e acessadas facilmente em qualquer outro script.
"""

settings = Settings()
