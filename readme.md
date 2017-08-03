# Image Assets Compiler

A Python Script for automating processing of source image assets from various resolutions or formats to web or native specific formats and sizes.

Author: [simondotm](https://github.com/simondotm)

## About

The script works recursively with folder structures and also handles date stamping to ensure only modified source assets are recompiled when run multiple times. 

The compiler is a python script, and requires Python 2.7 or later, with the [Pillow fork](https://python-pillow.org/) of [Python Imaging Library (PIL)](http://www.pythonware.com/products/pil/) installed.

## Usage
Create an `assets.json` file as described below.

Run compile.py to execute the script, it will scan the source `assets` folders and create the compiled assets in the `output` folder.

The script will preserve file folder structures from `assets` to `output`.


## Asset.json Settings

The script requires an `assets.json` file to be present in the root folder. This contains the following configurations:

* A path to the root "assets" folder where source assets are found
* A path to the "output" folder where compiled assets will be placed
* A list of folders under the root assets folder that will be scanned (the script automatically adds folders it finds to the `assets.json` file) and any properties for how to process each folder or file.

The script will auto generate an `assets.json` file if none exists.

Each folder can have properties applied to specify how all assets in that folder should be processed.

Specific files within a folder can have override properties too.

### Meta.json file
When the script is first run, it automatically creates a file called `meta.json` in the `output` folder. This file maintains a database of how each of the input files were last processed, so that the script can intelligently only re-process images that have either been modified or have had properties modified since the last time the script was run.

The `meta.json` file can be deleted, which will guarantee that all assets will be re-processed on the next run, as well as the `meta.json` file being automatically re-generated.

### Conversion Options
* `scale <p>` - scale image by p% (default 100%)
* `width <n>` - scale image proportionally to fixed pixel width, will scale up or down
* `height <n>` - scale image proportionally to fixed pixel height, will scale up or down
* `retina <0-3>` - output N upsampled versions of the asset, 0 = none (default), 1 = @2x, 2 = @4x, 3 = @8x etc.
* `square` <0/1> - force output image to be square (adds padding on smallest dimension)
* `pad <p>` - ensure a p% sized border exists (if square is selected, this border will be incorporated) (default 0%)
* `palette <0-256>` - reduce image to an indexed palette image of N colours (PNG images compress over 40% using this option)
* `invert <0/1>` - invert the image
* `alpha <0/1>` - create a white alpha mask version of the RGBA image
* `format <X>` - output the file in a specific file format

If only `width` or `height` is specified, aspect is maintained

If `width` AND `height` is specified, aspect is not maintained

Any specifed `width` or `height` overrides any `scale` setting

## Version Control

The script is fully compatible with version control, and there is no need to filter the meta.json file from the version control system.

It is also ok to add the output folder to version control too if desired.

## TODO

The script does not currently remove retina derivative files if the previous compile created them and the subsequent compile did not.

Support multiple output formats

Fix formats in the meta file if different to source to prevent always recompiling

Support dithering in colour conversion

