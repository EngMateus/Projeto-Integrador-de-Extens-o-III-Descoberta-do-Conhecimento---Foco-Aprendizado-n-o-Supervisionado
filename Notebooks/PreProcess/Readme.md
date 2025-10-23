# 🧹 preprocess.py — Normalização e Extração de Chaves

## 📘 Descrição Geral
O arquivo **`preprocess.py`** implementa a classe **`TextProcessor`**, responsável por realizar **limpeza, normalização e extração de identificadores (CPF/CNPJ)** em textos.  
É utilizada principalmente em processos de **pré-processamento**, garantindo que os textos e chaves sejam padronizados antes da indexação

A classe foi construída com **métodos estáticos**, permitindo seu uso sem necessidade de instância.

---

## ⚙️ Estrutura da Classe

### **Classe:** `TextProcessor`
> Centraliza as operações de normalização textual e extração de chaves de identificação (CPF/CNPJ do contratado).

---

### 🧩 `clean_text(text: str) -> str`
- **Função:** Limpa e normaliza o texto para uso em RAG.  
- **Etapas executadas:**
  - Remove quebras de linha (`\n`) e tabs (`\t`)
  - Substitui múltiplos espaços consecutivos por apenas um
  - Remove espaços extras no início e no fim
  - Mantém a capitalização original
- **Exemplo:**
  ```python
  TextProcessor.clean_text("Contrato\n\tde prestação   de serviços")
  # Saída: "Contrato de prestação de serviços"
  ```

---

### 🔤 `preprocess_text(text: str) -> str`
- **Função:** Aplica um pré-processamento simples para normalizar o texto.  
- **Etapas executadas:**
  - Converte o texto para letras minúsculas
  - Remove espaços extras
- **Exemplo:**
  ```python
  TextProcessor.preprocess_text("  EXEMPLO   DE   TEXTO  ")
  # Saída: "exemplo de texto"
  ```

---

### 🧱 `normalize_key(key: str) -> str`
- **Função:** Normaliza uma chave de identificação (CPF ou CNPJ).  
- **Etapas executadas:**
  - Remove todos os caracteres que não sejam letras ou números
- **Exemplo:**
  ```python
  TextProcessor.normalize_key("12.345.678/0001-01")
  # Saída: "123456789000101"
  ```

---

### 🔍 `extract_contractor_keys(text: str) -> Dict[str, str]`
- **Função:** Extrai o **CNPJ** e o **CPF** do contratado a partir do texto (primeira ocorrência de cada um).  
- **Retorno:** Dicionário com as chaves encontradas.
  ```python
  {
      "cnpj_contratado": "12345678900010",
      "cpf_contratado": "12345678910"
  }
  ```
- **Caso não sejam encontrados:**
  ```python
  {
      "cnpj_contratado": "SEM_CNPJ",
      "cpf_contratado": "SEM_CPF"
  }
  ```
- **Exemplo de uso:**
  ```python
  texto = "Contrato entre a empresa 12.345.678/0001-01 e o contratado 123.456.789-10."
  chaves = TextProcessor.extract_contractor_keys(texto)
  print(chaves)
  # Saída:
  # {'cnpj_contratado': '12345678900010', 'cpf_contratado': '12345678910'}
  ```

---

## 🧠 Observações
- Todos os métodos são **estáticos**, permitindo chamadas diretas:
  ```python
  TextProcessor.clean_text(texto)
  ```
- O módulo utiliza **expressões regulares (regex)** para identificar padrões de CPF e CNPJ formatados.


---

## ✅ Status
- Arquivo `preprocess.py` criado e documentado.  
- Classe `TextProcessor` implementada e funcional.  

