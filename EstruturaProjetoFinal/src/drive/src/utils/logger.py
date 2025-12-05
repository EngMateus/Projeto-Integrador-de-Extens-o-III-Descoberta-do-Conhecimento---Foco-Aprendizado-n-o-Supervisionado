import os
import time
import logging


class Logger:
    start_time = None

    @staticmethod
    def setup_logger(name="AppLogger", level=logging.INFO):
        """Configura um logger padrão para toda a aplicação."""
        os.makedirs("logs", exist_ok=True)
        logger = logging.getLogger(name)
        logger.setLevel(level)

        # Evita adicionar handlers duplicados
        if not logger.handlers:
            fh = logging.FileHandler("logs/app.log", encoding="utf-8")
            ch = logging.StreamHandler()

            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s')
            fh.setFormatter(formatter)
            ch.setFormatter(formatter)

            logger.addHandler(fh)
            logger.addHandler(ch)

        return logger

    @classmethod
    def start_timer(cls, logger):
        cls.start_time = time.time()
        logger.info("⏳ Iniciando processamento dos PDFs...")

    @classmethod
    def end_timer(cls, logger, total_processados):
        if cls.start_time is None:
            logger.warning("⚠️ Timer não iniciado corretamente.")
            return

        elapsed_time = time.time() - cls.start_time
        minutos = int(elapsed_time // 60)
        segundos = elapsed_time % 60

        logger.info(
            f"✅ Processamento finalizado: {total_processados} PDF(s) processado(s) "
            f"em {minutos}m {segundos:.2f}s."
        )
