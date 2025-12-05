from dotenv import load_dotenv  
load_dotenv() 

from src.drive_client import GoogleDriveClient
from src.pdf_processor import PDFProcessor
from src.pipeline_executor import PipelineExecutor
from src.utils.logger import Logger

def main():
    logger = Logger.setup_logger()

    # 1. Cliente do Google Drive
    drive_client = GoogleDriveClient(logger=logger)

    # 2. Processador de PDFs
    pdf_processor = PDFProcessor(
        drive_service=drive_client.service,
        logger=logger
    )

    # 3. Executor do pipeline
    pipeline = PipelineExecutor(
        drive_client=drive_client,
        pdf_processor=pdf_processor,
        max_workers=1,
        logger=logger
    )

    pipeline.executar()

if __name__ == "__main__":
    main()
