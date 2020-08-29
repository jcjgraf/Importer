# vim: ft=python fileencoding=utf-8 sw=4 et sts=4

from pathlib import Path
from typing import Any, Dict

from PyQt5.QtCore import QObject

from vimiv import api
from vimiv.utils import log


_logger = log.module_logger(__name__)


class ImportHandler(QObject):
    @api.objreg.register
    def __init__(self, info: str) -> None:
        super().__init__()

        self.options: Dict[str, str] = {}  # Dictionary storing all setting options

        for e in info.split(";"):
            option = e.split("=")
            self.options[self._sanatize(option[0])] = self._sanatize(option[1])
        _logger.debug("Initialized ImportHandler")

        try:
            destinationPath = Path(self.options["DestinationPath"])
            destinationPath.mkdir(parents=True, exist_ok=True)
            _logger.debug("Destination path already exists or created successfully")
        except KeyError:
            _logger.error("DestinationPath option is missing")
        except FileExistsError as error:
            _logger.error("Creating destination directory failed: %s", error)

    @api.commands.register()
    def importer(self) -> None:
        """Run importer."""
        _logger.debug("Import marked images")
        print(api.mark.paths)

    def _sanatize(self, option: str) -> str:
        """Remove potential whitespaces and quotes from `option`."""
        return option.strip().replace('"', "").replace("'", "")


def init(info: str, *_args: Any, **_kwargs: Any) -> None:
    """Setup import plugin by initializing the ImportHandler class."""
    ImportHandler(info)


def cleanup(*_args: Any, **_kwargs: Any) -> None:
    _logger.debug("Cleaning up importer plugin")
