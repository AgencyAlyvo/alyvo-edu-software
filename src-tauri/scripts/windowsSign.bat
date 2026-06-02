@echo off
echo =============================== >> log-windowsSign.txt
echo Current directory: %CD% >> log-windowsSign.txt
echo Signing file: %1 >> log-windowsSign.txt
echo Attempting to run: binarie-sign-windows\AzureSignTool.exe >> log-windowsSign.txt
binarie-sign-windows\AzureSignTool.exe sign %1 ^
    --azure-key-vault-url "%AZURE_KEY_VAULT_URL%" ^
    --azure-key-vault-client-id "%AZURE_KEY_VAULT_APP_CLIENT_ID%" ^
    --azure-key-vault-client-secret "%AZURE_KEY_VAULT_APP_CLIENT_SECRET%" ^
    --azure-key-vault-tenant-id "%AZURE_KEY_VAULT_TENANT_ID%" ^
    --azure-key-vault-certificate "%AZURE_KEY_VAULT_CERTIFICATE_NAME%" ^
    --timestamp-rfc3161 http://timestamp.digicert.com ^
    --timestamp-digest sha512 ^
    --file-digest sha512
if %ERRORLEVEL% NEQ 0 (
    echo Failed with error %ERRORLEVEL% >> log-windowsSign.txt
    echo =============================== >> log-windowsSign.txt
    exit /b %ERRORLEVEL%
)
echo Signing completed successfully >> log-windowsSign.txt
echo =============================== >> log-windowsSign.txt
