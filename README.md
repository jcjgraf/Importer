## Vimiv Importer
> [vimiv-qt](https://github.com/karlch/vimiv-qt) plugin for a consistent import workflow

Vimiv Importer lets you easily import images from a SD card, camera or any directory into your photo storage. The importer obeys your desired storage directory structure and image naming scheme.

### Installation
- Clone this project into `$XDG_DATA_HOME/vimiv/plugins/`
- Activate Vimiv Importer by adding to the `PLUGINS` section of `$XDG_CONFIG_HOME/vimiv/vimiv.conf`: `importer = option1=value1; option2=value2; ...`, where the following options exist:
    - `DestinationPath`: (required) the absolute root directory of the photo storage. E.g. `DestinationPath=/home/user/Images`
    - `DirectoryStructure`: (optional) the scheme by which the image are ordere in the `DestinationPath`. Available options are all option of [strftime](https://strftime.org/). Slashes designate the beginning of a new directory. E.g. `DirectoryStructure=Y/Ymd` may result in `2020/20200830/myImage.jpg`. If this option is left unset images get imported directly into the `DestinationPath` (without subfolders).
    - `ImageName`: (optional) the scheme by which the images are renamed during the import. Available options are all option of [strftime](https://strftime.org/). E.g `ImageName=Ymd` may result in `20200830.jpg`. If this option is left unset images are not renamed during the import.

### Usage
Mark all images you wish to import in vimiv and call `:importer`. That's it!

If there is a naming clash during the import the images first imported keeps its name. The second images gets a `-01` appended, the third clashing image a `-02` etc.

It is possible to add an additional, image specific identifier to the import path using the optional `--identifier` argument. For example, if `DirectoryStructure=Y/Ymd` and we use `:importer --identifier=MyBirthday` the images get imported into `Y/Ymd-MyBirthday/`.

When cleaning up the photo storage and deleting images it may happened that we delete `myImage.jpg` but keep `myImage-01.jpg`. To clean the naming the command `:importer-rearrange` can be used. It renames all images in the CDW according to the set naming schema.
