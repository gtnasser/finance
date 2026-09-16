import sys
import logging
from pathlib import Path
from loguru import logger

from config import settings

# Diretório para armazenamento dos arquivos de log
LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / settings.LOG_NAME


def setup_logger():
    """
    Configura o Loguru para Console/Arquivo com rotação e retenção.
    intercepta os logs padrão do Uvicorn/FastAPI.
    """
    # Remove manipuladores padrão do Loguru para evitar duplicidade
    logger.remove()

    # Em produção, desliga diagnose/backtrace para não vazar variáveis locais (ex: senhas)
    diagnose = not settings.is_production
    backtrace = not settings.is_production

    # Saída no terminal; Handler de Console (Estilo Logcat: Colorido e Detalhado); 
    logger.add(
        sys.stdout,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO",
    )

    print(LOG_FILE)

    # Handler de Arquivo
    logger.add(
        LOG_FILE,
        rotation=settings.LOG_ROTATION,
        retention=settings.LOG_RETENTION,
        compression="zip",
        encoding="utf-8",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="INFO",
        backtrace=backtrace,
        diagnose=diagnose,
    )

    # Interceptador para redirecionar logs nativos do Python (Uvicorn / FastAPI) para o Loguru
    class InterceptHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno

            frame, depth = logging.currentframe(), 2
            while frame and frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1

            logger.opt(depth=depth, exception=record.exc_info).log(
                level, record.getMessage()
            )

    # Aplica o InterceptHandler nos loggers do Uvicorn e FastAPI
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    for log_name in ("uvicorn", "uvicorn.access", "uvicorn.error", "fastapi"):
        logging_logger = logging.getLogger(log_name)
        logging_logger.handlers = [InterceptHandler()]

    logger.info(f"Sistema de logs inicializado em {LOG_DIR}.")
    return logger
