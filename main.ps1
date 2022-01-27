Set-Location -Path C:\iSIM\isimgui

$cmd = "C:/iSIM/isim_python_env/Scripts/python.exe"
Start-Process -File $cmd -WorkingDirectory "C:\iSIM\isimgui" -ArgumentList "-m main" #-WindowStyle Hidden  # This line will execute the cmd
Start-Sleep -Seconds 5