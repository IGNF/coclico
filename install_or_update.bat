REM Lancer dans Anaconda Prompt (pas powershell)
call windows_utils\get_conda.bat

mamba env update -n coclico -f environment.yml
