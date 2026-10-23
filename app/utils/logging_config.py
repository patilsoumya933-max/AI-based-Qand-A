"""Configure standard application logging."""

import logging


def configure_logging() -> None:
    """Set a consistent log format without logging user content or secrets."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )