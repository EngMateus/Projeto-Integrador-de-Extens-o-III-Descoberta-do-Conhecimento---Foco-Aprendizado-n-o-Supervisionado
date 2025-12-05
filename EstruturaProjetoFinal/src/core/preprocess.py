import re
from typing import Dict

class TextProcessor:
    """
    Classe para normalização de texto e extração de chaves específicas (CPF/CNPJ do contratado)
    """

    @staticmethod
    def clean_text(text: str) -> str:
        """
        Limpa e normaliza o texto para RAG:
        - Remove múltiplos espaços e quebras de linha
        - Remove tabs e espaços extras no início/fim
        - Mantém a capitalização original (pode ser ajustado se quiser minúsculas)
        """
        if not text:
            return ""
        # -> Substitui quebras de linha e tabs por espaço
        text = re.sub(r'[\n\t]+', ' ', text)
        # -> Remove múltiplos espaços consecutivos
        text = re.sub(r'\s+',' ', text)
        return text.strip()

    @staticmethod
    def preprocess_text(text: str) -> str:
        """
        Versão simples de pré-processamento:
        - Converte para minúsculas
        - Remove espaços extras
        """
        if not text:
            return ""
        text = text.lower()
        text = re.sub(r'\s+', ' ', text).strip() 
        return text

    @staticmethod
    def normalize_key(key: str) -> str:
        """
        Normaliza uma chave (CPF ou CNPJ):
        - Remove qualquer caractere que não seja número ou letra
        """
        if not key:
            return ""
        return re.sub(r'[^\w\d]', '', key.strip())

    @staticmethod
    def extract_contractor_keys(text: str) -> Dict[str, str]:
        """
        Extrai o CNPJ e CPF do contratado (primeira ocorrência de cada um).
        Retorna um dicionário:
        {
            "cnpj_contratado": "53502564000199",
            "cpf_contratado": "07231424910"
        }
        """
        # -> Padrões regex para CPF e CNPJ formatados
        cnpj_pattern = r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}'
        cpf_pattern = r'\d{3}\.\d{3}\.\d{3}-\d{2}'

        def _normalize_number(number: str) -> str:
            """
            Remove qualquer caractere que não seja número
            """
            return re.sub(r'[^0-9]', '', number)

        cnpjs = re.findall(cnpj_pattern, text)
        cpfs = re.findall(cpf_pattern, text)

        cnpj_contratado = _normalize_number(cnpjs[0]) if cnpjs else "SEM_CNPJ"
        cpf_contratado = _normalize_number(cpfs[0]) if cpfs else "SEM_CPF"

        return {
            "cnpj_contratado": cnpj_contratado,
            "cpf_contratado": cpf_contratado
        }