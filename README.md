# Projeto Integrador de Extensão III – Descoberta do Conhecimento Foco Aprendizado Não Supervisionado  Tema: RAG para Documentos Jurídicos

## 👥 Equipe
- Mateus Silva  
- Kevin Vinícius  

## 🎓 Curso
Ciência de Dados – 4º Período (2025) - Faculdade Donaduzzi

---

## 🧠 Descrição do Projeto

**RAG – Documentos Jurídicos** é uma plataforma inteligente baseada na arquitetura **Retrieval-Augmented Generation (RAG)** que permite realizar consultas em **linguagem natural** sobre documentos jurídicos, como leis, contratos, pareceres e sentenças.

Utilizando técnicas avançadas de inteligência artificial, o sistema realiza a **recuperação semântica** de trechos relevantes e gera **respostas precisas e contextualizadas**, promovendo acesso ágil e confiável à informação jurídica.

### 👤 Cliente
Departamento Jurídico – **Biopark**

---

## 🎯 Objetivos do Projeto


Este projeto visa a criação de uma ferramenta de IA baseada em RAG, desenhada especificamente para facilitar a pesquisa em documentos jurídicos. A plataforma irá processar consultas em linguagem natural, identificar e extrair informações relevantes de uma base de conhecimento jurídica (composta por leis, contratos e sentenças), e gerar respostas confiáveis e bem fundamentadas, otimizando a busca por informações jurídicas.

### ✅ Objetivos Específicos

- Aplicar teoria na prática por meio do desenvolvimento de uma plataforma inteligente.
- Desenvolver competências técnicas e comportamentais, como:
  - Trabalho em equipe
  - Comunicação eficaz
  - Liderança e colaboração
- Estimular o pensamento crítico e criativo na resolução de problemas reais.
- Preparar os alunos para o mercado de trabalho e/ou projetos de pesquisa e extensão.

---



### Descrição Técnica Inicial

O projeto será desenvolvido em **Python** e implementado como uma plataforma inteligente baseada na arquitetura **Geração Aumentada por Recuperação (RAG)**. O sistema terá como objetivo processar consultas em linguagem natural sobre uma base de conhecimento jurídica, recuperando informações e gerando respostas precisas e contextualizadas.

A solução técnica será estruturada nas seguintes etapas:

* **Fonte de Dados:** Utilizaremos documentos jurídicos diversos, como leis, contratos, sentenças e pareceres, em possíveis formatos como csv, excel, pdf e imagens, para criar a base de conhecimento do sistema. Esses documentos serão armazenados na pasta `/data`.

* **Pré-processamento:** O texto dos documentos será processado para extrair o conteúdo relevante e segmentá-lo em pequenos trechos ("chunks"). Essa etapa visa otimizar a busca por informações.

* **Embeddings e Armazenamento Vetorial:**
    * Modelos de embedding  serão utilizados para converter cada "chunk" de texto em vetores numéricos.
    * Esses vetores serão armazenados em um **banco de dados vetorial**, que permitirá a busca eficiente e rápida por similaridade semântica.

* **Fluxo de Consulta (RAG):**
    * O usuário fará uma consulta em linguagem natural.
    * A consulta será convertida em um vetor usando o mesmo modelo de embedding.
    * O sistema buscará no banco de dados vetorial os trechos dos documentos jurídicos que são mais semanticamente similares à consulta.
    * Os trechos recuperados, juntamente com a pergunta original, serão enviados a um **Large Language Model (LLM)** (como o modelo Gemini ou uma API do OpenAI) para gerar a resposta final, garantindo que ela seja precisa e contextualizada com base na fonte original.
