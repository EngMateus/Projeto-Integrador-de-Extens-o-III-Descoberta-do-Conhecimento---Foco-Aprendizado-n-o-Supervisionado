from concurrent.futures import ThreadPoolExecutor, as_completed

class PipelineExecutor:
    """Orquestra o fluxo de download e extração em paralelo."""

    def __init__(self, drive_client, pdf_processor, max_workers=5, logger=None):
        self.drive_client = drive_client
        self.pdf_processor = pdf_processor
        self.max_workers = max_workers
        self.logger = logger

    def executar(self):
        """Executa o pipeline completo de forma paralela."""
        arquivos = self.drive_client.listar_pdfs()
        self.logger.info(f"Iniciando processamento de {len(arquivos)} PDFs...")

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futuros = [
                executor.submit(self.pdf_processor.download_pdf, item['id'], item['name'])
                for item in arquivos

            ]

            for futuro in as_completed(futuros):
                try:
                    resultado = futuro.result()
                    self.logger.info(f"✅ Processado: {resultado}")
                except Exception as e:
                    self.logger.error(f"Erro no processamento: {e}")
