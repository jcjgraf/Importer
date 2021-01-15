# vim: ft=python fileencoding=utf-8 sw=4 et sts=4

from datetime import datetime
import os
from os import path
from pathlib import Path
import re
from shutil import copy2
from typing import Any

from vimiv import api, utils
from vimiv.utils import log
from vimiv.imutils import exif


_logger = log.module_logger(__name__)


class ImportHandler:

    DestinationPath: Path = None
    DirectorySchema: str = None
    ImageNameSchema: str = None
    ClearMark: bool = True
    PostInstall: str = None

    num_padding: int = 2

    @api.objreg.register
    def __init__(self, info: str) -> None:

        # Extract options from info string and save to global variables
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
    def importer(self, identifier="") -> None:
        """Run importer.

        Copy all marked images to the configured destination and order them in
        the provided structure. Rename image according to the provided image
        name scheme.

        Args:
            identifier: If set it gets appended to the name of the image folder.
        """
        _logger.debug(f"Import marked images. identifier={identifier}")

        images = api.mark.paths.copy()

        if self.ClearMark:
            api.mark.mark_clear()

        self._importer(images, identifier)

    # TODO: Call _importer directly, but nested decorators do not seems to work
    @utils.asyncfunc()
    def _importer(self, images: [str], identifier=""):

        if not images:
            _logger.info("No image marked. Please mark images to import")
            return

        suffix = f"-{identifier}" if identifier else ""

        new_files = list()

        for image in images:

            try:
                base_path = self._get_directory_structure(image, suffix)
                base_path.mkdir(parents=True, exist_ok=True)
                _logger.debug(
                    "Photo directory %s created successfully or already existed",
                    base_path,
                )

                name = self._get_image_name(image, base_path)

                # TODO: Not race-condition save
                copy2(str(Path(image)), base_path / name)
                _logger.debug("Copied %s to %s", image, base_path / name)

                new_files.append(str(base_path / name))

            except FileExistsError as error:
                _logger.error(
                    "Creating image directory %s failed: %s", base_path, error
                )

        _logger.debug("Imported all images")

        if self.PostInstall:
            _logger.debug("Starting Hook")
            os.system(eval(self.PostInstall))
            _logger.debug("Hook Ended")

    @api.commands.register()
    def importer_rearrange(self) -> None:
        """Rearranges image in CWD accoring to configured schema."""

        images = api.pathlist()

        for image in images:

            base_path = Path(path.split(image)[0])

            name = self._get_image_name(image, base_path)

            if image == str(base_path / name):
                continue

            os.rename(image, base_path / name)
            _logger.debug(f"Rename {image} to {name}")

    def _get_directory_structure(self, image, suffix: str) -> Path:
        """Generate the destination path for a current image.

        Args:
            suffix: word appended to the name of the image folder
        """

        date = datetime.strptime(
            exif.ExifHandler(image).exif_date_time(), "%Y:%m:%d %H:%M:%S"
        )

        # Turn DirectorySchema into valid strftime by prepending % to the format codes
        structure = re.sub(r"([a-zA-Z])", "%\\g<0>", self.DirectorySchema)
        return self.DestinationPath / (date.strftime(structure) + suffix)

    def _get_image_name(
        self, image: str, dest_dir: Path = None, uniquify: bool = True
    ) -> str:
        """Generate the image name according to the configured scheme.

        If uniquify is set to True and dest_dir is set, then dest_dir is examined to
        make sure that the image name is unique in base_dir. If not, a number is
        appended to the name.

        Args:
            image: path to the image
            dest_dir: directory to consider for uniqueness
            uniquify: if set a count is appended to make to image unique
        """

        assert (not uniquify) or (uniquify and dest_dir)

        if not self.ImageNameSchema:
            _logger.debug("No ImageNameSchema provided, keep current image name")
            return path.split(image)[1]

        date = datetime.strptime(
            exif.ExifHandler(image).exif_date_time(), "%Y:%m:%d %H:%M:%S"
        )

        ext = path.splitext(image)[1]
        # Turn ImageNameSchema into valid strftime by prepending % to the format codes
        name = date.strftime(re.sub(r"([a-zA-Z])", "%\\g<0>", self.ImageNameSchema))

        # If the file is itself
        if (
            not uniquify
            or not path.isfile(dest_dir / (name + ext))
            or image == str(dest_dir / (name + ext))
        ):
            return name + ext

        # Add counter
        name = name + f"_%0{self.num_padding}d" + ext

        count = 1

        # While the file exists but is it not the file itself
        while path.isfile(dest_dir / (name % count)) and not image == str(
            dest_dir / (name % count)
        ):
            count += 1

        return name % count

    def _getSanatized(self, option: str) -> str:
        """Remove potential white spaces and quotes from `option`."""
        # return option.strip().replace('"', "").replace("'", "")
        return option.strip()


def init(info: str, *_args: Any, **_kwargs: Any) -> None:
    """Setup import plugin by initializing the ImportHandler class."""
    ImportHandler(info)
