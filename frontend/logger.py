import sys
from pathlib import Path
from loguru import logger

# Parametros para rotação e retenção
LOG_ROTATION = "10 MB"
LOG_RETENTION = "14 days"

# Diretório para armazenamento dos arquivos de log
LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "financing.log"

def setup_logger():
    """Configura o Loguru para interceptação de eventos no Streamlit."""

    # Remove manipuladores padrão do Loguru para evitar duplicidade
    logger.remove()

    # Saída no terminal; Handler de Console (Estilo Logcat: Colorido e Detalhado); 
    logger.add(
        sys.stdout,
        colorize=True,
        format="<blue>{time:YYYY-MM-DD HH:mm:ss}</blue> | <level>{level: <8}</level> | <level>{message}</level>",
        level="DEBUG",
    )

    # Gravação em arquivo específico da UI
    logger.add(
        LOG_FILE,
        rotation=LOG_ROTATION,
        retention=LOG_RETENTION,
        compression="zip",
        encoding="utf-8",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        level="INFO",
        backtrace=True,
        diagnose=True,
    )
    logger.info(f"Sistema de logs inicializado em {LOG_DIR}.")
    return logger

    # O Streamlit não disponibiliza interceptadores, então implementaremos o registro do log
    # na classe APIClient, método get()

logger = setup_logger()
