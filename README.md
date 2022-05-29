# Data tools

## Introduction

This repository contains data tools for exporting from labelme format to a different one. There are also some tools for the dataset in general (sorting based on view, validating annotations).

All python scripts were tested with Python 3.7.10.

**As of now, only Windows is supported for starting labelme.**

## How to install

Simply clone this repository. Use `update.bat` in the `tools` directory to update to the latest commit.

## Repository structure

- The `data` directory is for your dataset.
- The `anno_data` directory is for your annotation files.
- **All scripts are in the `tools` directory.**
  - `start_labelme.bat` [starts labelme](##Running-labelme) (annotation program).
  - `update.bat` fetches and pulls the repository (updates to the latest version).
  - `export.py` [exports](##Export) data set annotations to another formats.
  - `validate.py` [validates](##Validate) annotations.
  - `datatools` python module contains internal python code.
  - `_labelme` directory contains config for labelme.

## Running labelme

You need to have labelme for annotation:

```powershell
pip install labelme
```

Double click `start_labelme.bat` or use the command line:

```powershell
start_labelme.bat <optional: specify a picture directory>
```

The default directory is `anno_data` in the root directory. It is not recommended to change this default.

## Export

Currently, `export.py` supports exporting to [YOLOv4](https://github.com/AlexeyAB/Yolo_mark/issues/60#issuecomment-401854885) and [vehicle attributes](https://github.com/openvinotoolkit/training_extensions/tree/misc/misc/tensorflow_toolkit/vehicle_attributes) formats.

### Usage

Write into the terminal:

```powershell
python export.py -h
```

(you might have to change `python` to `python3` if you are not on Windows).

That will show you all the possible formats. For help on export arguments, use the `-h` or `--help` flags after a format:

```powershell
python export.py <format> --help
```

Default data directory is `.\data`. To include data directory in export, prefix it with an ❗. Use the `--help` flag for information for all arguments.

## Validate

not done yet 😔
<!-- TODO: write documentation after validate script is finished -->

## Saving past commands

If you specify the `-S` flag right after a script, your arguments will be saved into a `last_<script>_args.txt` file.
For example:

```powershell
python export.py -S yolo --exec="..\..\darknet\darknet.exe"
```

After that, if you run the script without arguments, it will use the ones in the `.txt` file.
