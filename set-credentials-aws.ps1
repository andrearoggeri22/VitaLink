Write-Host "`nAWS CREDENTIALS CONFIGURATION" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan

function Get-CurrentCredential {
    param ([string]$ConfigKey)
    
    try {
        $value = aws configure get $ConfigKey 2>$null
        return $value
    }
    catch {
        return $null
    }
}

function Set-AWSCredential {
    param (
        [string]$Key,
        [string]$Value
    )
    
    Write-Host "Setting: $Key" -ForegroundColor Yellow
    
    try {
        aws configure set $Key $Value
        Write-Host "Credential configured: $Key" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "Error configuring $Key : $_" -ForegroundColor Red
        return $false
    }
}

$credentials = @(
    @{
        Key = "aws_access_key_id"
        Prompt = "AWS Access Key ID"
        Help = "Get from AWS Academy Lab details"
        Required = $true
        Secure = $false
    },
    @{
        Key = "aws_secret_access_key"
        Prompt = "AWS Secret Access Key"
        Help = "Get from AWS Academy Lab details"
        Required = $true
        Secure = $true
    },
    @{
        Key = "aws_session_token"
        Prompt = "AWS Session Token"
        Help = "Get from AWS Academy Lab details (expires every 3 hours)"
        Required = $true
        Secure = $true
    },
    @{
        Key = "region"
        Prompt = "AWS Region"
        Help = "Default region for AWS operations"
        Default = "us-east-1"
        Required = $false
        Secure = $false
    },
    @{
        Key = "output"
        Prompt = "Output Format"
        Help = "CLI output format"
        Default = "json"
        Required = $false
        Secure = $false
    }
)

Write-Host "AWS Academy Lab Session Setup" -ForegroundColor Yellow
Write-Host "Get credentials from AWS Academy Lab Details page" -ForegroundColor Yellow
Write-Host "`nFor each credential you can:" -ForegroundColor Yellow
Write-Host "- Enter a new value" -ForegroundColor Yellow
Write-Host "- Press ENTER to keep existing value" -ForegroundColor Yellow
Write-Host "- Press ENTER to use default value (if available)" -ForegroundColor Yellow

$configuredCount = 0
$totalCount = $credentials.Count

foreach ($cred in $credentials) {
    Write-Host "`n"
    Write-Host "Credential: $($cred.Prompt)" -ForegroundColor Cyan
    Write-Host "Key: $($cred.Key)" -ForegroundColor Gray
    Write-Host "Help: $($cred.Help)" -ForegroundColor Yellow
    
    $existingValue = Get-CurrentCredential -ConfigKey $cred.Key
    $hasExisting = ![string]::IsNullOrWhiteSpace($existingValue)
    
    if ($hasExisting) {
        if ($cred.Secure) {
            $maskedValue = $existingValue.Substring(0, [Math]::Min(6, $existingValue.Length)) + "..."
            Write-Host "Current value: $maskedValue" -ForegroundColor Green
        }
        else {
            Write-Host "Current value: $existingValue" -ForegroundColor Green
        }
    }
    else {
        Write-Host "Current value: [NOT CONFIGURED]" -ForegroundColor Red
    }
    
    if ($cred.Default -and -not $hasExisting) {
        Write-Host "Default value: $($cred.Default)" -ForegroundColor Blue
    }
    
    $promptMessage = if ($hasExisting) {
        "New value (ENTER to keep existing)"
    }
    elseif ($cred.Default) {
        "Value (ENTER for default)"
    }
    else {
        "Value"
    }
    
    if ($cred.Secure) {
        $newValue = Read-Host "$promptMessage" -AsSecureString
        $newValuePlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($newValue))
    }
    else {
        $newValuePlain = Read-Host "$promptMessage"
    }
    
    $finalValue = $null
    
    if ([string]::IsNullOrWhiteSpace($newValuePlain)) {
        if ($hasExisting) {
            Write-Host "Keeping existing value" -ForegroundColor Blue
            continue
        }
        elseif ($cred.Default) {
            $finalValue = $cred.Default
            Write-Host "Using default value: $finalValue" -ForegroundColor Blue
        }
        elseif ($cred.Required) {
            Write-Host "This credential is required!" -ForegroundColor Red
            continue
        }
        else {
            Write-Host "Credential skipped (optional)" -ForegroundColor Yellow
            continue
        }
    }
    else {
        $finalValue = $newValuePlain
        Write-Host "New value set" -ForegroundColor Green
    }
    
    if (Set-AWSCredential -Key $cred.Key -Value $finalValue) {
        $configuredCount++
    }
}

Write-Host "`n"
Write-Host "CONFIGURATION SUMMARY" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "Credentials configured: $configuredCount/$totalCount" -ForegroundColor Green

Write-Host "`nTesting AWS connection..." -ForegroundColor Yellow
try {
    $identity = aws sts get-caller-identity | ConvertFrom-Json
    Write-Host "SUCCESS: Connected to AWS" -ForegroundColor Green
    Write-Host "Account ID: $($identity.Account)" -ForegroundColor Green
    Write-Host "User ARN: $($identity.Arn)" -ForegroundColor Green
    
    $region = aws configure get region
    Write-Host "Region: $region" -ForegroundColor Green
}
catch {
    Write-Host "ERROR: Failed to connect to AWS" -ForegroundColor Red
    Write-Host "Please check your credentials and try again" -ForegroundColor Red
}

Write-Host "`nNEXT STEPS" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "1. Configure application secrets:" -ForegroundColor Yellow
Write-Host "   .\set-params-aws.ps1" -ForegroundColor White
Write-Host "2. Setup CloudFormation:" -ForegroundColor Yellow
Write-Host "   .\set-cloudformation-aws.ps1" -ForegroundColor White

Write-Host "`nIMPORTANT NOTES" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "- AWS Academy session tokens expire every 3 hours" -ForegroundColor Yellow
Write-Host "- Re-run this script when tokens expire" -ForegroundColor Yellow
Write-Host "- Always get fresh credentials from AWS Academy Lab Details" -ForegroundColor Yellow

Write-Host "`nAWS CREDENTIALS CONFIGURATION COMPLETED"