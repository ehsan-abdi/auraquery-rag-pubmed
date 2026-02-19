# app/utils/logging.py
import logging
import sys


def setup_logging(level: str = "INFO") -> None:
    """
    Configure global logging settings.
    All modules should use logging.getLogger(__name__).
    """
    log_format = (
        "[%(asctime)s] [%(levelname)s] [%(name)s] "
        "- %(message)s"
    )
    logging.basicConfig(
        level=level.upper(),
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Optionally: suppress verbose logs from 3rd-party libs
    logging.getLogger("Bio").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
