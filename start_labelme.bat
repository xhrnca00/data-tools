@echo off
SETLOCAL

if "%~1" neq "" (
    set "dir=%~1"
) else (
    set "dir=!*"
)

@echo on

labelme %dir% --labels .labelme/labels.txt --labelflags .labelme/labelflags.json --nodata --autosave --validatelabel exact
