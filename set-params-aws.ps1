Write-Host "`nVITALINK SECRETS CONFIGURATION" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan

$environment = "production"
$region = aws configure get region

Write-Host "Environment: $environment" -ForegroundColor Green
Write-Host "AWS Region: $region" -ForegroundColor Green

Write-Host "`nChecking AWS credentials..." -ForegroundColor Yellow
try {
    $identity = aws sts get-caller-identity | ConvertFrom-Json
    Write-Host "Connected as: $($identity.Arn)" -ForegroundColor Green
}
catch {
    Write-Host "ERROR: Invalid AWS credentials. Run 'aws configure' before continuing." -ForegroundColor Red
    exit 1
}

function Get-ExistingParameter {
    param (
        [string]$ParameterName
    )
    
    try {
        $result = aws ssm get-parameter --name $ParameterName --with-decryption 2>$null | ConvertFrom-Json
        return $result.Parameter.Value
    }
    catch {
        return $null
    }
}

function Set-ParameterValue {
    param (
        [string]$Name,
        [string]$Value,
        [string]$Type,
        [string]$Description
    )
    
    Write-Host "Configuring: $Name" -ForegroundColor Yellow
    
    try {
        aws ssm put-parameter --name $Name --value $Value --type $Type --description $Description --overwrite | Out-Null
        Write-Host "Parameter configured: $Name" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "Error configuring $Name : $_" -ForegroundColor Red
        return $false
    }
}

function Generate-SecurePassword {
    param ([int]$Length = 32)
    
    $chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^*"
    $password = ""
    for ($i = 0; $i -lt $Length; $i++) {
        $password += $chars[(Get-Random -Maximum $chars.Length)]
    }
    return $password
}

$parameters = @(
    @{
        Name = "/vitalink/$environment/fitbit/client-id"
        Type = "SecureString"
        Description = "Fitbit API Client ID"
        Prompt = "Fitbit Client ID"
        Help = "Get from: https://dev.fitbit.com/apps"
        Required = $false
    },
    @{
        Name = "/vitalink/$environment/fitbit/client-secret"
        Type = "SecureString"
        Description = "Fitbit API Client Secret"
        Prompt = "Fitbit Client Secret"
        Help = "Get from: https://dev.fitbit.com/apps"
        Required = $false
    },
    @{
        Name = "/vitalink/$environment/fitbit/redirect-uri"
        Type = "String"
        Description = "Fitbit OAuth Redirect URI"
        Prompt = "Fitbit Redirect URI"
        Help = "Example: https://your-domain.com/auth/fitbit/callback"
        Default = "http://localhost:5000/auth/fitbit/callback"
        Required = $false
    },
    @{
        Name = "/vitalink/$environment/mailjet/api-key"
        Type = "SecureString"
        Description = "Mailjet API Key"
        Prompt = "Mailjet API Key"
        Help = "Get from: https://app.mailjet.com/account/apikeys"
        Required = $false
    },
    @{
        Name = "/vitalink/$environment/mailjet/secret"
        Type = "SecureString"
        Description = "Mailjet API Secret"
        Prompt = "Mailjet API Secret"
        Help = "Get from: https://app.mailjet.com/account/apikeys"
        Required = $false
    },
    @{
        Name = "/vitalink/$environment/email/sender"
        Type = "String"
        Description = "Email sender address"
        Prompt = "Email Sender"
        Help = "Email address verified in Mailjet"
        Default = "noreply@vitalink.com"
        Required = $false
    },
    @{
        Name = "/vitalink/$environment/session/secret"
        Type = "SecureString"
        Description = "Flask Session Secret Key"
        Prompt = "Session Secret"
        Help = "Secret key for Flask sessions (leave empty to auto-generate)"
        AutoGenerate = $true
        Required = $false
    },
    @{
        Name = "/vitalink/$environment/jwt/secret"
        Type = "SecureString"
        Description = "JWT Secret Key"
        Prompt = "JWT Secret"
        Help = "Secret key for JWT tokens (leave empty to auto-generate)"
        AutoGenerate = $true
        Required = $false
    }
)

Write-Host "`nPARAMETERS CONFIGURATION" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "For each parameter you can:" -ForegroundColor Yellow
Write-Host "- Enter a new value" -ForegroundColor Yellow
Write-Host "- Press ENTER to keep the existing value" -ForegroundColor Yellow
Write-Host "- Press ENTER to use the default value (if available)" -ForegroundColor Yellow
Write-Host "- For auto-generable secrets, leave empty to auto-generate" -ForegroundColor Yellow

$configuredCount = 0
$totalCount = $parameters.Count

foreach ($param in $parameters) {
    Write-Host "`n"
    Write-Host "Parameter: $($param.Prompt)" -ForegroundColor Cyan
    Write-Host "Path: $($param.Name)" -ForegroundColor Gray
    Write-Host "Type: $($param.Type)" -ForegroundColor Gray
    Write-Host "Help: $($param.Help)" -ForegroundColor Yellow
    
    $existingValue = Get-ExistingParameter -ParameterName $param.Name
    $hasExisting = $existingValue -ne $null
    
    if ($hasExisting) {
        if ($param.Type -eq "SecureString") {
            Write-Host "Existing value: [HIDDEN]" -ForegroundColor Green
        }
        else {
            Write-Host "Existing value: $existingValue" -ForegroundColor Green
        }
    }
    else {
        Write-Host "Existing value: [NOT CONFIGURED]" -ForegroundColor Red
    }
    
    if ($param.Default -and -not $hasExisting) {
        Write-Host "Default value: $($param.Default)" -ForegroundColor Blue
    }
    
    $promptMessage = if ($hasExisting) {
        "New value (ENTER to keep existing)"
    }
    elseif ($param.Default) {
        "Value (ENTER for default)"
    }
    elseif ($param.AutoGenerate) {
        "Value (ENTER to auto-generate)"
    }
    else {
        "Value"
    }
    
    if ($param.Type -eq "SecureString" -and -not $param.AutoGenerate) {
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
        elseif ($param.Default) {
            $finalValue = $param.Default
            Write-Host "Using default value: $finalValue" -ForegroundColor Blue
        }
        elseif ($param.AutoGenerate) {
            $finalValue = Generate-SecurePassword
            Write-Host "Auto-generated: [HIDDEN]" -ForegroundColor Blue
        }
        elseif ($param.Required) {
            Write-Host "This parameter is required!" -ForegroundColor Red
            continue
        }
        else {
            Write-Host "⏭Parameter skipped (optional)" -ForegroundColor Yellow
            continue
        }
    }
    else {
        $finalValue = $newValuePlain
        Write-Host "New value set" -ForegroundColor Green
    }
    
    if (Set-ParameterValue -Name $param.Name -Value $finalValue -Type $param.Type -Description $param.Description) {
        $configuredCount++
    }
}

Write-Host "`n"
Write-Host "CONFIGURATION SUMMARY" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "Configured parameters: $configuredCount/$totalCount" -ForegroundColor Green

Write-Host "`nCheck configured parameters:" -ForegroundColor Yellow
$configuredParams = @()

foreach ($param in $parameters) {
    $exists = Get-ExistingParameter -ParameterName $param.Name
    if ($exists) {
        $configuredParams += $param.Name
        Write-Host "$($param.Name)" -ForegroundColor Green
    }
    else {
        Write-Host "$($param.Name)" -ForegroundColor Red
    }
}

Write-Host "`nNEXT STEPS" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "1. You can proceed with CloudFormation deployment:" -ForegroundColor Yellow
Write-Host "   .\set-cloudformation-aws.ps1" -ForegroundColor White