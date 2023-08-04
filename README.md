# iSIM Control

Python Control Interface for the iSIM at LEB-EPFL

## Installation

### Assumptions

- Windows PC
- Python 3.9.5 is installed

### Steps

1. Create a folder called on the PC called `C:\iSIM\`.
1. Install **Micro-Manager 2.0.1 20220523** into `C:\iSIM\Micro-Manager-2.0.2`.
1. Clone this repo to `C:\iSIM\isimgui` on the control PC.
1. Copy `MMStartup.bsh` from this repo to the Micro-Manager folder.
1. Install the necessary Micro-Manager plugins from https://github.com/wl-stepp/micro-manager-isim by copying the .jar files into `C:\iSIM\Micro-Manager-2.0.2\mmplugins`.
1. Create a new Python virtual environment with the following command. Note the directory! `python -m venv C:\iSIM\isim_python_env`.
1. Activate the virtual environment in a Powershell console: `C:\iSIM\isim_python_env\Scripts\Activate.ps1`.
1. Move into the cloned repository: `Set-Location C:\iSIM\isimgui`.
1. Install the control software: `pip install .`
1. Create a shortcut to `C:\iSIM\Micro-Manager-2.0.2\ImageJ.exe` on the Desktop if it doesn't already exist.
