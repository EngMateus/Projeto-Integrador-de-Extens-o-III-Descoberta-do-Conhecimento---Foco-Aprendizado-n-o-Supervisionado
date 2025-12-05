# flask_app.py

from flask import Flask, request, jsonify, render_template, redirect, url_for, send_file, Response, stream_with_context
from src.rag.rag_pipeline import RAGPipeline
from src.ingestion.pdf_indexer import PDFIndexer
from src.core.logger_config import setup_logger
from src.core.preprocess import TextProcessor
from src.config.settings import settings
from src.core.models import Advogado
from src.core.db import db
from pathlib import Path
import fitz  # PyMuPDF
import re

# Imports para Streaming
from queue import Queue, Empty 
from threading import Thread 
from langchain.callbacks.base import BaseCallbackHandler
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore

BASE_DIR = Path(__file__).resolve().parent.parent.parent
PDF_DIR = BASE_DIR / "src" / "drive" / "extraidos"

# Callback para capturar tokens da IA
class QueueCallback(BaseCallbackHandler):
    def __init__(self, q: Queue): self.q = q
    def on_llm_new_token(self, token: str, **kwargs) -> None: self.q.put(token)
    def on_llm_end(self, *args, **kwargs) -> None: self.q.put(None)
    def on_llm_error(self, error: Exception, **kwargs) -> None:
        self.q.put(f"Erro: {error}")
        self.q.put(None)

def create_app() -> Flask:
    app = Flask(__name__, template_folder=str(BASE_DIR / "templates"), static_folder=str(BASE_DIR / "static"))
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{BASE_DIR / 'advogados.db'}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    
    logger = setup_logger("projeto_rag")
    rag = RAGPipeline(logger=logger)
    indexer = PDFIndexer(logger=logger)

    with app.app_context():
        db.create_all()
        if not Advogado.query.filter_by(oab_cpf="12345678912").first():
            adv = Advogado(oab_cpf="12345678912", senha="senha123")
            db.session.add(adv); db.session.commit()

    # --- MANTIDA A BUSCA HÍBRIDA V7 (PERFEITA) ---
    def search_pdfs_by_query(query: str):
        matches = set()
        q_raw = query.strip(); q_lower = q_raw.lower()
        SCORE_THRESHOLD = 0.70 
        q_nums = re.sub(r'\D', '', q_raw)
        is_numeric_search = len(q_nums) in [11, 14] 

        if settings.PINECONE_API_KEY:
            try:
                embeddings = OpenAIEmbeddings(model=settings.EMBEDDING_MODEL)
                vectorstore = PineconeVectorStore(index_name=settings.PINECONE_INDEX_NAME, embedding=embeddings, text_key="text")
                pinecone_candidates = []

                if is_numeric_search:
                    filter_field = "cnpj_contratado" if len(q_nums) == 14 else "cpf_contratado"
                    results = vectorstore.similarity_search(q_raw, k=50, filter={filter_field: q_nums})
                    for doc in results:
                        if doc.metadata.get("source_file"): pinecone_candidates.append(doc.metadata.get("source_file").lower().strip())
                else:
                    results = vectorstore.similarity_search_with_score(q_raw, k=50)
                    for doc, score in results:
                        name = doc.metadata.get("source_file", "").lower().strip()
                        if q_lower in name or score >= SCORE_THRESHOLD: # Resgate por nome ou score
                            pinecone_candidates.append(name)

                if pinecone_candidates:
                    for pdf_file in PDF_DIR.glob("*.pdf"):
                        local_stem = pdf_file.stem.lower().replace('.', ' ').strip()
                        for p_name in pinecone_candidates:
                            if p_name in local_stem or local_stem in p_name:
                                matches.add(pdf_file.name); break
            except Exception as e: logger.error(f"Erro Pinecone: {e}")

        if not is_numeric_search:
            for pdf_file in PDF_DIR.glob("*.pdf"):
                if pdf_file.name in matches: continue
                try:
                    with fitz.open(pdf_file) as doc:
                        if doc.page_count > 0:
                            if q_lower in "".join([p.get_text() for p in doc]).lower(): matches.add(pdf_file.name)
                except: pass
        return sorted(list(matches))

    def preview_pdf(pdf_file_name: str):
        path = PDF_DIR / pdf_file_name
        if not path.exists(): return ""
        try:
            with fitz.open(path) as doc: return "".join([p.get_text() for p in doc])
        except: return ""

    # Rotas Padrão
    @app.route("/")
    def home(): return redirect(url_for("login_page"))
    @app.route("/login")
    def login_page(): return render_template("login.html")
    @app.route("/loading")
    def loading_page(): return render_template("loading.html")
    @app.route("/Site_Pergunta.html")
    def chatbot_page(): return render_template("site_pergunta.html")
    
    @app.route("/auth", methods=["POST"])
    def auth():
        data = request.json or {}
        adv = Advogado.query.filter_by(oab_cpf=data.get("oab_cpf", "").strip()).first()
        if adv and adv.senha == data.get("senha", "").strip():
            return jsonify({"success": True, "redirect": url_for("loading_page")})
        return jsonify({"success": False}), 400

    @app.route("/search_pdf", methods=["POST"])
    def search_pdf():
        return jsonify({"pdfs": search_pdfs_by_query((request.json or {}).get("query", "").strip())})

    @app.route("/preview_pdf", methods=["POST"])
    def preview_pdf_route():
        return jsonify({"preview": preview_pdf((request.json or {}).get("pdf_file", ""))})

    @app.route("/view_pdf", methods=["GET"])
    def view_pdf():
        return send_file(PDF_DIR / request.args.get("pdf_file", ""), mimetype="application/pdf")

    @app.route("/index", methods=["POST"])
    def index_route():
        indexer.index_pdfs()
        return jsonify({"status": "started"})

    # --- ROTA ASK COM STREAMING ---
    @app.route("/ask", methods=["POST"])
    def ask():
        data = request.json or {}
        question = data.get("question", "").strip()
        pdf_selected = data.get("pdf_selected", "").strip()
        user_input = data.get("user_input", "").strip()

        if not question or not pdf_selected:
            return jsonify({"response": "Dados inválidos."}), 400

        filter_key = {}
        norm_input = TextProcessor.normalize_key(user_input)
        if norm_input.isdigit():
            if len(norm_input) == 14: filter_key = {"cnpj_contratado": norm_input}
            elif len(norm_input) == 11: filter_key = {"cpf_contratado": norm_input}
        else:
            filter_key = {"source_file": pdf_selected}

        def generate():
            q = Queue()
            callback = QueueCallback(q)
            try:
                qa_chain = rag.get_qa_chain(question, filter_key)
            except Exception as e:
                yield f"Erro setup: {e}"; return

            def run_thread():
                with app.app_context():
                    try: qa_chain.invoke({"query": question}, config={"callbacks": [callback]})
                    except Exception as e: q.put(f"Erro: {e}")
                    finally: q.put(None)

            t = Thread(target=run_thread); t.start()
            
            while True:
                try:
                    token = q.get(timeout=3)
                    if token is None: break
                    yield token
                except Empty: continue
                except Exception: break
            t.join()

        return Response(stream_with_context(generate()), mimetype='text/plain')

    return app