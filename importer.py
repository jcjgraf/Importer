# vim: ft=python fileencoding=utf-8 sw=4 et sts=4

from datetime import datetime
from pathlib import Path
import re
from typing import Any, Dict

from PyQt5.QtCore import QObject

from vimiv import api
from vimiv.utils import log
from vimiv.imutils import exif


_logger = log.module_logger(__name__)


class ImportHandler(QObject):

    DestinationPath: Path = None
    DirectoryStructure: str = None
    ImageName: str = None

    @api.objreg.register
    def __init__(self, info: str) -> None:
        super().__init__()

        self.options: Dict[str, str] = {}  # Dictionary storing all setting options

        for e in info.split(";"):
            key, value = e.split("=")
            key, value = self._getSanatized(key), self._getSanatized(value)
            if not hasattr(self, key):
                _logger.warning("Provided option %s is invalid", key)
            else:
                if key == "DestinationPath":
                    value = Path(value)
                setattr(self, key, value)
        _logger.debug("Initialized ImportHandler")

        try:
            if not self.DestinationPath:
                raise AttributeError("`DestinationPath` is not set")
            self.DestinationPath.mkdir(parents=True, exist_ok=True)
            _logger.debug("Destination path already exists or created successfully")
        except AttributeError:
            _logger.error("Destination path option is missing")
        except FileExistsError as error:
            _logger.error("Creating destination path directory failed: %s", error)

    @api.commands.register()
    def importer(self) -> None:
        """Run importer."""
        _logger.debug("Import marked images")

        if not api.mark.paths:
            _logger.info("No image marked. Please mark images to import")
            return

        for image in api.mark.paths:
            date = datetime.strptime(exif.exif_date_time(image), "%Y:%m:%d %H:%M:%S")

            try:
                imageDir = self._generateDirectoryStructure(date)
                imageDir.mkdir(parents=True, exist_ok=True)
                _logger.debug(
                    "Photo directory %s created successfully or already existed",
                    imageDir,
                )
            except FileExistsError as error:
                _logger.error("Creating image directory %s failed: %s", imageDir, error)

    def _generateDirectoryStructure(self, date: datetime) -> Path:
        """Generate the testination path for a certain image

        Args:
            date: datetime of the current image
        """

        structure = re.sub(r"([a-zA-Z])", "%\\g<0>", self.DirectoryStructure)
        return self.DestinationPath / date.strftime(structure)

    def _getSanatized(self, option: str) -> str:
        """Remove potential whitespaces and quotes from `option`."""
        return option.strip().replace('"', "").replace("'", "")


def init(info: str, *_args: Any, **_kwargs: Any) -> None:
    """Setup import plugin by initializing the ImportHandler class."""
    ImportHandler(info)


def cleanup(*_args: Any, **_kwargs: Any) -> None:
    _logger.debug("Cleaning up importer plugin")
