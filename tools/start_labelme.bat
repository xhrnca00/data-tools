@echo off
SETLOCAL

if "%~1" neq "" (
    set "dir=%~1"
) else (
    set "dir=%~dp0\..\anno_data"
)

@echo on

labelme %dir% --labels %~dp0\_labelme\labels.txt --labelflags %~dp0\_labelme\labelflags.json --nodata --autosave --validatelabel exact
