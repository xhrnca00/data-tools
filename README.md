# Labelme config

## Introduction

This repository contains configuration and exporting files for labelme (exporting labelme data to other formats).

**So far, only Windows is supported for starting labelme.**

## How to install

Simply clone this repository. When starting labelme using the batch files, all the files will update to the latest commit.

## Running labelme

Double click the `start_labelme.bat` or use the command line:

```powershell
./start_labelme.bat <optional: specify a picture directory>
```

## Deprecated

`start_labelme_legacy.bat` is deprecated and exports files in a different format. `export.py` can still parse it, but it is turned off by default.

## Export files

Currently, `export.py` supports exporting to [YOLOv4](https://github.com/AlexeyAB/Yolo_mark/issues/60#issuecomment-401854885) and [vehicle attributes](https://github.com/openvinotoolkit/training_extensions/tree/misc/misc/tensorflow_toolkit/vehicle_attributes) formats.

### Usage

Write into the terminal:

```powershell
python export.py -h
```

(you might have to change `python` to `python3` if you are not on Windows). That will show you all the possible commands.

Point `export.py` at your data directory and make sure all folders with data are prefixed with an exclamation mark (❗) (can be changed). You can also just doubleclick (will use this directory).

Default export format is YOLO.
