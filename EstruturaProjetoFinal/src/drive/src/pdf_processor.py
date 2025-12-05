import os
import time
import io
import random
from googleapiclient.http import MediaIoBaseDownload
# from PyPDF2 import PdfReader 

class PDFProcessor:
    def __init__(self, drive_service, logger, output_dir="extraidos"):
        self.service = drive_service
        self.logger = logger
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def download_pdf(self, file_id, file_name, max_retries=3):
        """Baixa o PDF do Google Drive com retry, backoff e VALIDAÇÃO de arquivo vazio."""
        output_path = os.path.join(self.output_dir, file_name)

        # --- MELHORIA: Validar se o arquivo existente não está vazio ---
        if os.path.exists(output_path):
            try:
                if os.path.getsize(output_path) > 0:
                    self.logger.info(f"⏩ Pulando download (já existe e não está vazio): {file_name}")
                    return output_path
                else:
                    self.logger.warning(f"⚠️ Arquivo existente está vazio. Baixando novamente: {file_name}")
                    os.remove(output_path) # Remove o arquivo vazio
            except OSError as e:
                self.logger.warning(f"Não foi possível verificar o arquivo existente {file_name}: {e}. Baixando novamente.")
        # --- Fim da Melhoria ---

        for attempt in range(1, max_retries + 1):
            try:
                start_time = time.time()
                request = self.service.files().get_media(fileId=file_id)
                fh = None
                download_succeeded = False # Flag para rastrear o sucesso

                # --- CORREÇÃO ESTRUTURAL (try/except/finally) ---
                try:
                    fh = io.FileIO(output_path, "wb")
                    downloader = MediaIoBaseDownload(fh, request)
                    done = False
                    while not done:
                        status, done = downloader.next_chunk()
                        # (Opcional) Log de progresso pode ser muito verboso
                        # if status:
                        #    self.logger.info(f"📥 Download {int(status.progress() * 100)}% para {file_name}")
                    
                    download_succeeded = True # Marcar sucesso apenas se o loop terminar
                except Exception as e:
                    self.logger.error(f"❌ Erro durante o chunk do download {file_name} (tentativa {attempt}): {e}")
                    # Não re-lance, deixe o 'finally' limpar e o 'for' tentar novamente
                finally:
                    if fh:
                        fh.close() # Sempre feche o arquivo
                
                # --- CORREÇÃO PRINCIPAL: Validação Pós-Download ---
                if download_succeeded:
                    # Verifica se o arquivo foi criado E se tem conteúdo
                    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                        # SUCESSO REAL
                        elapsed = time.time() - start_time
                        self.logger.info(f"✅ Download concluído: {file_name} ({elapsed:.2f}s)")
                        return output_path # Retorna o caminho e sai do loop 'for'
                    else:
                        # Download "concluído" mas o arquivo está vazio
                        self.logger.warning(f"⚠️ Download de {file_name} concluído, mas o arquivo está vazio. (Tentativa {attempt}/{max_retries})")
                        if os.path.exists(output_path):
                            os.remove(output_path) # Limpa o arquivo vazio
                
                # Se 'download_succeeded' for False ou o arquivo for vazio,
                # o código continua para o 'except' externo para acionar o retry.
                if not download_succeeded:
                    raise Exception("Falha no download (erro no chunk)")
                else:
                    raise Exception("Falha no download (arquivo vazio)")
                
            except Exception as e:
                # Este 'except' agora pega erros do 'get_media' E as falhas de validação
                wait = 2 ** attempt + random.uniform(0, 1)
                self.logger.error(f"❌ Erro ao baixar {file_name} (tentativa {attempt}/{max_retries}): {e}")
                if attempt < max_retries:
                    self.logger.warning(f"🔁 Re-tentando em {wait:.1f}s...")
                    time.sleep(wait)
                else:
                    self.logger.error(f"🚫 Falha definitiva ao baixar {file_name}")
                    return None # Falha definitiva
        
        return None # Caso o loop 'for' termine sem sucesso