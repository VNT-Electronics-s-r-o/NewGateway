:: This is a batch file that will run the assembly_gateway.py script. It runs the script in the virtual environment that is created by the gatevenv folder. This batch file is used to run the script on a Windows machine.
:: pip install -r /path/to/requirements.txt
::@echo off
::cd /d "C:\GatewayAssemblyUploader\GatewayAssembly\"
::call C:\GatewayAssemblyUploader\GatewayAssembly\gatevenv\Scripts\activate
::python C:\GatewayAssemblyUploader\GatewayAssembly\assembly_gateway.py

::@echo off
::cd /d "C:\GatewayAssemblyUploader\GatewayAssembly\"

:: Activate virtual environment
::call C:\GatewayAssemblyUploader\GatewayAssembly\gatevenv\Scripts\activate

:: Run your Python script
::python C:\GatewayAssemblyUploader\GatewayAssembly\assembly_gateway.py

:: Deactivate virtual environment
::deactivate

::@echo off
::cd /d "C:\GatewayAssemblyUploader\GatewayAssembly\"

:: Activate virtual environment and run Python script
::call C:\GatewayAssemblyUploader\GatewayAssembly\gatevenv\Scripts\activate && C:\path\to\python3.12.exe C:\GatewayAssemblyUploader\GatewayAssembly\assembly_gateway.py

:: Deactivate virtual environment (this may not be necessary, but added for completeness)
::deactivate

::python3.12 -m venv --help
::python3.12 -m ensurepip --default-pip
::python3.12 -m venv venv_name
::\venv_name\Scripts\activate

::virtualenv venv –python=python3.12

::# Create virtual environment with Python 3.11 version
::python -m virtualenv -p D:\Python311\python.exe my_second_env

::Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy Unrestricted


::conda env create -f environment.yml
::conda activate gatevenv


@echo off

rem Set the path to your Anaconda or Miniconda installation
::set CONDA_PATH=C:\Users\Pruvodky\anaconda3
set CONDA_PATH=C:\Users\Pruvodky\anaconda3

rem Set the name of your Conda environment
set ENV_NAME=newGWEnv

echo Activating Conda environment: %ENV_NAME%
rem Activate the Conda environment
call %CONDA_PATH%\Scripts\activate %ENV_NAME%

rem Set the Python executable path within the Conda environment
set PYTHON_EXECUTABLE=%CONDA_PREFIX%\python.exe

echo Running Python script: C:\NewGW\main.py
rem Run your main Python program using the specified Python executable
%PYTHON_EXECUTABLE% C:\NewGW\main.py

echo Deactivating Conda environment: %ENV_NAME%
rem Deactivate the Conda environment when done
call %CONDA_PATH%\Scripts\deactivate

