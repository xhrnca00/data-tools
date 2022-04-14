# Labelme config

## Introduction

This repository contains configuration and export files for labelme (exporting labelme data to other format)

## How to install

Simply clone this repository. When starting labelme using the batch files, all the files will update to the latest commit.

## Running on Windows

Double click the `start_labelme.bat` or use the command line:

```powershell
./start_labelme.bat <optional: specify a picture directory>
```

## Deprecated

`start_labelme_legacy.bat` is deprecated and exports files in a different format. `export.py` can still parse it, but it is turned off by default.
