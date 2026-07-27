import logging
from logging.handlers import RotatingFileHandler

import pytest

from chatbot.logger_config import configure_logging


@pytest.fixture
def isolated_logging(tmp_path, monkeypatch):
    """Run logging setup in a temp cwd and restore the root logger afterwards."""
    monkeypatch.chdir(tmp_path)
    root = logging.getLogger()
    original_handlers = list(root.handlers)
    original_level = root.level

    yield tmp_path

    for handler in root.handlers:
        handler.close()
    root.handlers = original_handlers
    root.setLevel(original_level)


def test_configure_logging_creates_console_and_file_handlers(isolated_logging):
    configure_logging()

    handlers = logging.getLogger().handlers

    assert any(isinstance(handler, RotatingFileHandler) for handler in handlers)
    assert any(type(handler) is logging.StreamHandler for handler in handlers)


def test_configure_logging_writes_to_the_logs_directory(isolated_logging):
    configure_logging()

    logging.getLogger("test").info("hello from the test suite")
    for handler in logging.getLogger().handlers:
        handler.flush()

    log_file = isolated_logging / "logs" / "chatbot.log"
    assert log_file.is_file()
    assert "hello from the test suite" in log_file.read_text(encoding="utf-8")


def test_configure_logging_respects_the_requested_level(isolated_logging):
    configure_logging(logging.WARNING)

    assert logging.getLogger().level == logging.WARNING


def test_configure_logging_is_idempotent(isolated_logging):
    configure_logging()
    configure_logging()

    assert len(logging.getLogger().handlers) == 2
