@echo off
SETLOCAL

:: get latest version
git fetch && git pull

if "%~1" neq "" (
    set "dir=%~1"
) else (
    set "dir=."
)

@echo on

labelme %dir% --labels _labelme/labels.txt --labelflags _labelme/labelflags.json --nodata --autosave --validatelabel exact
