@echo off
setlocal enabledelayedexpansion

:: Default file arguments
set "EXAMPLE_FILE=%~1"
set "ENV_FILE=%~2"
if "%EXAMPLE_FILE%"=="" set "EXAMPLE_FILE=.env.example"
if "%ENV_FILE%"=="" set "ENV_FILE=.env"

:: Check if example file exists
if not exist "%EXAMPLE_FILE%" (
    echo ❌ %EXAMPLE_FILE% not found. Cannot configure environment. >&2
    exit /b 1
)

:: Create .env if missing by copying the example
if not exist "%ENV_FILE%" (
    copy "%EXAMPLE_FILE%" "%ENV_FILE%" >nul
)

echo 🔧 Configuring environment variables from %EXAMPLE_FILE%
echo (Press Enter to accept the shown value. Leave blank to clear optional values.)
echo.

:: Process each line in the example file
for /f "usebackq tokens=*" %%A in ("%EXAMPLE_FILE%") do (
    set "line=%%A"
    :: Skip empty lines and comments
    if not "!line!"=="" (
        echo !line! | findstr /r "^[[:space:]]*#" >nul
        if errorlevel 1 (
            :: Extract key (everything before first =)
            for /f "tokens=1 delims==" %%B in ("!line!") do (
                set "key=%%B"
                set "key=!key: =!"
                if not "!key!"=="" (
                    call :process_key "!key!"
                )
            )
        )
    )
)

echo ✅ Environment configured and saved to %ENV_FILE%
exit /b 0

:process_key
set "key=%~1"

:: Skip ADT_UTILS_REPO - automatically use default value without prompting
if "%key%"=="ADT_UTILS_REPO" (
    call :get_current_value "%key%" current_value
    call :get_default_value "%key%" default_value
    if "!current_value!"=="" (
        set "value=!default_value!"
    ) else (
        set "value=!current_value!"
    )
    call :update_env_file "%key%" "!value!"
    echo ✅ ADT_UTILS_REPO automatically set to: !value!
    goto :eof
)

:: Handle ADTS interactively - collect one by one
if "%key%"=="ADTS" (
    echo 🔗 Setting up ADTS (Accessible Digital Textbooks)
    echo Enter ADT repository URLs one by one. Press Enter with empty input to finish.
    echo.
    
    :: Get current ADTS value
    call :get_current_value "%key%" current_adts
    
    :: Show current ADTs if they exist
    if not "!current_adts!"=="" (
        echo Current ADTs:
        set "adt_count=0"
        for %%A in (!current_adts!) do (
            set /a "adt_count+=1"
            echo   !adt_count!. %%A
        )
        echo.
    ) else (
        set "adt_count=0"
    )
    
    :: Collect new ADTs
    echo Add new ADTs (or press Enter to keep current list):
    set "adts_list=!current_adts!"
    
    :adt_input_loop
    set /a "adt_count+=1"
    set /p "adt_input=- Enter ADT #!adt_count! URL (or press Enter to finish): "
    
    if "!adt_input!"=="" goto :adt_done
    
    :: Add to list (space-separated)
    if "!adts_list!"=="" (
        set "adts_list=!adt_input!"
    ) else (
        set "adts_list=!adts_list! !adt_input!"
    )
    echo   ✅ Added: !adt_input!
    goto :adt_input_loop
    
    :adt_done
    set "value=!adts_list!"
    call :update_env_file "%key%" "!value!"
    
    :: Count final ADTs for confirmation
    set "final_count=0"
    if not "!value!"=="" (
        for %%A in (!value!) do set /a "final_count+=1"
        echo ✅ ADTS configured with !final_count! repositories
    ) else (
        echo ✅ ADTS left empty
    )
    goto :eof
)

:: Get current and default values
call :get_current_value "%key%" current_value
call :get_default_value "%key%" default_value

if "!current_value!"=="" (
    set "show=!default_value!"
) else (
    set "show=!current_value!"
)

:: Truncate sensitive values for display
if "%key%"=="OPENAI_API_KEY" (
    if not "!show!"=="" (
        set "show=!show:~0,15!..."
    )
)
if "%key%"=="GITHUB_TOKEN" (
    if not "!show!"=="" (
        set "show=!show:~0,15!..."
    )
)

:input_loop
set /p "input=- Enter value for %key% [!show!]: "

:: Required key enforcement
if "%key%"=="OPENAI_API_KEY" (
    if "!input!"=="" if "!current_value!"=="" (
        set /p "input=  (Required) Enter value for %key%: "
    )
)
if "%key%"=="OPENAI_MODEL" (
    if "!input!"=="" if "!current_value!"=="" (
        set /p "input=  (Required) Enter value for %key%: "
    )
)

if "!input!"=="" (
    set "value=!show!"
) else (
    set "value=!input!"
)

:: Skip validation if value is empty
if "!value!"=="" goto :update_value

:: Validate the input value
call :validate_env_value "%key%" "!value!"
if errorlevel 1 (
    echo   Please enter a valid value.
    set "show="
    goto :input_loop
)

:update_value
call :update_env_file "%key%" "!value!"
goto :eof

:get_current_value
set "search_key=%~1"
set "result="
for /f "usebackq tokens=2 delims==" %%C in (`findstr /b /c:"%search_key%=" "%ENV_FILE%" 2^>nul`) do (
    set "result=%%C"
)
set "%~2=!result!"
goto :eof

:get_default_value
set "search_key=%~1"
set "result="
for /f "usebackq tokens=2 delims==" %%D in (`findstr /b /c:"%search_key%=" "%EXAMPLE_FILE%" 2^>nul`) do (
    set "result=%%D"
)
set "%~2=!result!"
goto :eof

:validate_env_value
set "val_key=%~1"
set "val_value=%~2"

if "%val_key%"=="OPENAI_API_KEY" (
    if not "!val_value!"=="" (
        echo !val_value! | findstr /b /c:"sk-" >nul
        if errorlevel 1 (
            echo ❌ OPENAI_API_KEY must start with 'sk-'
            exit /b 1
        )
    )
)

if "%val_key%"=="GITHUB_TOKEN" (
    if not "!val_value!"=="" (
        echo !val_value! | findstr /b /c:"github_pat" >nul
        if errorlevel 1 (
            echo ❌ GITHUB_TOKEN must start with 'github_pat'
            exit /b 1
        )
    )
)

exit /b 0

:update_env_file
set "upd_key=%~1"
set "upd_value=%~2"

:: Check if key exists in file
findstr /b /c:"%upd_key%=" "%ENV_FILE%" >nul 2>&1
if errorlevel 1 (
    :: Key doesn't exist, append it
    echo.>> "%ENV_FILE%"
    echo %upd_key%=%upd_value%>> "%ENV_FILE%"
) else (
    :: Key exists, replace it
    set "temp_file=%TEMP%\env_temp_%RANDOM%.txt"
    (
        for /f "usebackq tokens=*" %%E in ("%ENV_FILE%") do (
            set "env_line=%%E"
            echo !env_line! | findstr /b /c:"%upd_key%=" >nul
            if errorlevel 1 (
                echo !env_line!
            ) else (
                echo %upd_key%=%upd_value%
            )
        )
    ) > "!temp_file!"
    move "!temp_file!" "%ENV_FILE%" >nul
)
goto :eof