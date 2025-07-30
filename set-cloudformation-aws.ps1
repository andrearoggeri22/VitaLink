Write-Host "`nVITALINK MANUAL DEPLOYMENT" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan

function Get-CurrentStackStatus {
    param ([string]$StackName)
    
    try {
        $result = aws cloudformation describe-stacks --stack-name $StackName 2>$null | ConvertFrom-Json
        return $result.Stacks[0].StackStatus
    }
    catch {
        return $null
    }
}

function Test-DockerRunning {
    try {
        docker info | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

function Test-HealthEndpoint {
    param ([string]$Url, [int]$MaxRetries = 12, [int]$IntervalSeconds = 20)
    
    for ($i = 1; $i -le $MaxRetries; $i++) {
        Write-Host "Health check attempt $i of $MaxRetries..." -ForegroundColor Yellow
        
        try {
            $response = Invoke-WebRequest -Uri $Url -TimeoutSec 10 -ErrorAction SilentlyContinue
            
            if ($response.StatusCode -eq 200) {
                Write-Host "Application is healthy!" -ForegroundColor Green
                Write-Host "Response: $($response.Content)" -ForegroundColor Gray
                return $true
            }
            else {
                Write-Host "Application responded with status $($response.StatusCode), waiting..." -ForegroundColor Yellow
            }
        }
        catch {
            Write-Host "Application not yet available, waiting..." -ForegroundColor Yellow
        }
        
        if ($i -lt $MaxRetries) {
            Start-Sleep -Seconds $IntervalSeconds
        }
    }
    
    Write-Host "Could not verify application health" -ForegroundColor Red
    return $false
}

function Monitor-StackDeployment {
    param ([string]$StackName)
    
    Write-Host "Monitoring stack deployment..." -ForegroundColor Yellow
    $resourcesCompleted = @{}
    $startTime = Get-Date
    
    do {
        Start-Sleep -Seconds 30
        try {
            $stackStatus = aws cloudformation describe-stacks --stack-name $StackName | ConvertFrom-Json
            $status = $stackStatus.Stacks[0].StackStatus
            
            $events = aws cloudformation describe-stack-events --stack-name $StackName | ConvertFrom-Json
            
            foreach ($eventAWS in $events.StackEvents) {
                if (($eventAWS.ResourceStatus -eq "CREATE_COMPLETE") -and (-not $resourcesCompleted.ContainsKey($eventAWS.LogicalResourceId))) {
                    $resourcesCompleted[$eventAWS.LogicalResourceId] = $true
                }
            }
            
            $elapsed = (Get-Date) - $startTime
            $elapsedStr = "{0:hh\:mm\:ss}" -f $elapsed
            
            Write-Host "Status: $status | Resources created: $($resourcesCompleted.Count) | Time: $elapsedStr" -ForegroundColor Yellow
            
            $latestEvent = $events.StackEvents | Select-Object -First 1
            if ($latestEvent.ResourceStatus -eq "CREATE_IN_PROGRESS") {
                Write-Host "Creating: $($latestEvent.LogicalResourceId)" -ForegroundColor Cyan
            }
            elseif ($latestEvent.ResourceStatus -eq "CREATE_COMPLETE") {
                Write-Host "Completed: $($latestEvent.LogicalResourceId)" -ForegroundColor Green
            }
            
            if ($status -like "*FAILED*" -or $status -like "*ROLLBACK*") {
                Write-Host "`nDeployment failed, checking events..." -ForegroundColor Red
                $errorEvents = $events.StackEvents | Where-Object { $_.ResourceStatus -like "*FAILED*" } | Select-Object -First 3
                
                if ($errorEvents) {
                    Write-Host "Recent errors:" -ForegroundColor Red
                    foreach ($eventAWS in $errorEvents) {
                        Write-Host "Resource: $($eventAWS.LogicalResourceId), Status: $($eventAWS.ResourceStatus)" -ForegroundColor Red
                        Write-Host "Reason: $($eventAWS.ResourceStatusReason)" -ForegroundColor Red
                    }
                }
                return $false
            }
            
            if ($status -eq "CREATE_COMPLETE") {
                return $true
            }
        }
        catch {
            Write-Host "Error checking stack status: $_" -ForegroundColor Red
        }
    } while ($status -like "*_IN_PROGRESS")
    
    return $false
}

$deploymentConfig = @(
    @{
        Key = "RepoName"
        Prompt = "ECR Repository Name"
        Help = "Name for the ECR repository"
        Default = "vitalink"
        Required = $false
    },
    @{
        Key = "StackName"
        Prompt = "CloudFormation Stack Name"
        Help = "Name for the CloudFormation stack"
        Default = "VitaLink-Stack"
        Required = $false
    },
    @{
        Key = "TemplatePath"
        Prompt = "Template Path"
        Help = "Path to the CloudFormation template"
        Default = "C:\Users\andre\git\VitaLink\vitalink-infrastructure.yaml"
        Required = $false
    },
    @{
        Key = "ProjectRoot"
        Prompt = "Project Root Directory"
        Help = "Root directory of the VitaLink project"
        Default = "C:\Users\andre\git\VitaLink"
        Required = $false
    },
    @{
        Key = "DatabasePassword"
        Prompt = "Database Password"
        Help = "Password for the PostgreSQL database"
        Default = "VitaLink2025!DB#Pass"
        Required = $false
        Secure = $true
    },
    @{
        Key = "Environment"
        Prompt = "Environment"
        Help = "Deployment environment"
        Default = "production"
        Required = $false
    },
    @{
        Key = "DesiredTaskCount"
        Prompt = "Desired Task Count"
        Help = "Number of ECS tasks to run"
        Default = "1"
        Required = $false
    }
)

Write-Host "Configure deployment parameters" -ForegroundColor Yellow
Write-Host "For each parameter you can:" -ForegroundColor Yellow
Write-Host "- Enter a new value" -ForegroundColor Yellow
Write-Host "- Press ENTER to use default value" -ForegroundColor Yellow

$parameters = @{}
$configuredCount = 0

foreach ($config in $deploymentConfig) {
    Write-Host "`n"
    Write-Host "Parameter: $($config.Prompt)" -ForegroundColor Cyan
    Write-Host "Help: $($config.Help)" -ForegroundColor Yellow
    Write-Host "Default: $($config.Default)" -ForegroundColor Blue
    
    $promptMessage = "Value (ENTER for default)"
    
    if ($config.Secure) {
        $newValue = Read-Host "$promptMessage" -AsSecureString
        $newValuePlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($newValue))
    }
    else {
        $newValuePlain = Read-Host "$promptMessage"
    }
    
    if ([string]::IsNullOrWhiteSpace($newValuePlain)) {
        $parameters[$config.Key] = $config.Default
        Write-Host "Using default value: $($config.Default)" -ForegroundColor Blue
    }
    else {
        $parameters[$config.Key] = $newValuePlain
        Write-Host "Custom value set" -ForegroundColor Green
    }
    
    $configuredCount++
}

Write-Host "`n"
Write-Host "CONFIGURATION SUMMARY" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "Parameters configured: $configuredCount/$($deploymentConfig.Count)" -ForegroundColor Green

Write-Host "`nValidating prerequisites..." -ForegroundColor Yellow

$validationErrors = @()

try {
    $identity = aws sts get-caller-identity | ConvertFrom-Json
    Write-Host "AWS credentials valid" -ForegroundColor Green
    Write-Host "Connected as: $($identity.Arn)" -ForegroundColor Gray
    Write-Host "Account ID: $($identity.Account)" -ForegroundColor Gray
}
catch {
    $validationErrors += "Invalid AWS credentials"
}

$awsRegion = aws configure get region
Write-Host "AWS Region: $awsRegion" -ForegroundColor Gray

if (-not (Test-DockerRunning)) {
    $validationErrors += "Docker is not running"
}
else {
    Write-Host "Docker is running" -ForegroundColor Green
}

if (-not (Test-Path $parameters.TemplatePath)) {
    $validationErrors += "Template file not found: $($parameters.TemplatePath)"
}
else {
    Write-Host "Template file found" -ForegroundColor Green
}

if (-not (Test-Path $parameters.ProjectRoot)) {
    $validationErrors += "Project directory not found: $($parameters.ProjectRoot)"
}
else {
    Write-Host "Project directory found" -ForegroundColor Green
}

if ($validationErrors.Count -gt 0) {
    Write-Host "`nVALIDATION ERRORS" -ForegroundColor Red
    Write-Host "=================================================" -ForegroundColor Red
    foreach ($errorAWS in $validationErrors) {
        Write-Host "- $errorAWS" -ForegroundColor Red
    }
    Write-Host "`nPlease fix the errors above and try again" -ForegroundColor Red
    exit 1
}

Write-Host "`nValidation successful" -ForegroundColor Green

Write-Host "`nPHASE 1: DOCKER PREPARATION" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan

Write-Host "Checking ECR repository..." -ForegroundColor Yellow
$repoExists = $false
$repoUri = $null

try {
    $repoCheck = aws ecr describe-repositories --repository-names $parameters.RepoName 2>$null
    if ($repoCheck) {
        $repoExists = $true
        $repoUri = (($repoCheck | ConvertFrom-Json).repositories | Where-Object { $_.repositoryName -eq $parameters.RepoName }).repositoryUri
        Write-Host "ECR repository exists: $repoUri" -ForegroundColor Green
    }
}
catch {
    Write-Host "ECR repository not found, will create..." -ForegroundColor Yellow
}

if (-not $repoExists) {
    Write-Host "Creating ECR repository..." -ForegroundColor Yellow
    try {
        $ecrResult = aws ecr create-repository --repository-name $parameters.RepoName | ConvertFrom-Json
        $repoUri = $ecrResult.repository.repositoryUri
        Write-Host "ECR repository created: $repoUri" -ForegroundColor Green
    }
    catch {
        Write-Host "ERROR creating ECR repository: $_" -ForegroundColor Red
        exit 1
    }
}

Write-Host "Logging into ECR..." -ForegroundColor Yellow
try {
    $loginToken = aws ecr get-login-password --region $awsRegion
    $loginToken | docker login --username AWS --password-stdin $repoUri.Split('/')[0]
    Write-Host "ECR login completed" -ForegroundColor Green
}
catch {
    Write-Host "ERROR logging into ECR: $_" -ForegroundColor Red
    exit 1
}

Write-Host "Building Docker image..." -ForegroundColor Yellow
Set-Location $parameters.ProjectRoot
try {
    docker build -t "$($parameters.RepoName):latest" .
    Write-Host "Docker build completed" -ForegroundColor Green
}
catch {
    Write-Host "ERROR building Docker image: $_" -ForegroundColor Red
    exit 1
}

$sourceImage = "$($parameters.RepoName):latest"
$targetImage = "${repoUri}:latest"

Write-Host "Tagging Docker image..." -ForegroundColor Yellow
docker tag $sourceImage $targetImage

Write-Host "Pushing image to ECR..." -ForegroundColor Yellow
try {
    docker push $targetImage
    Write-Host "Push to ECR completed: $targetImage" -ForegroundColor Green
}
catch {
    Write-Host "ERROR pushing to ECR: $_" -ForegroundColor Red
    exit 1
}

Write-Host "`nPHASE 2: CLOUDFORMATION VALIDATION" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan

Write-Host "Validating CloudFormation template..." -ForegroundColor Yellow
try {
    $validation = aws cloudformation validate-template --template-body file://$($parameters.TemplatePath) | ConvertFrom-Json
    Write-Host "Template validated successfully" -ForegroundColor Green
    
    Write-Host "Template parameters:" -ForegroundColor Green
    foreach ($param in $validation.Parameters) {
        $defaultValue = if ($param.DefaultValue) { $param.DefaultValue } else { "(no default)" }
        Write-Host "  $($param.ParameterKey): $defaultValue" -ForegroundColor Gray
    }
}
catch {
    Write-Host "ERROR validating template: $_" -ForegroundColor Red
    exit 1
}

Write-Host "`nPHASE 3: ENVIRONMENT CLEANUP" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan

Write-Host "Checking for existing stacks..." -ForegroundColor Yellow
$stackExists = $false
$stackStatus = $null

$existingStatus = Get-CurrentStackStatus -StackName $parameters.StackName
if ($existingStatus) {
    $stackExists = $true
    $stackStatus = $existingStatus
    Write-Host "Existing stack found: $($parameters.StackName) (Status: $stackStatus)" -ForegroundColor Yellow
    
    $response = Read-Host "Do you want to delete the existing stack and redeploy? (y/N)"
    if ($response -match "^[Yy]") {
        Write-Host "Deleting existing stack..." -ForegroundColor Yellow
        aws cloudformation delete-stack --stack-name $parameters.StackName
        
        Write-Host "Waiting for stack deletion..." -ForegroundColor Yellow
        do {
            Start-Sleep -Seconds 15
            $deleteStatus = Get-CurrentStackStatus -StackName $parameters.StackName
            if ($deleteStatus) {
                Write-Host "Deletion status: $deleteStatus" -ForegroundColor Yellow
            }
            else {
                Write-Host "Stack deleted successfully" -ForegroundColor Green
                break
            }
        } while ($deleteStatus)
    }
    else {
        Write-Host "Deployment cancelled by user" -ForegroundColor Yellow
        exit 0
    }
}
else {
    Write-Host "No existing stack found" -ForegroundColor Green
}

Write-Host "`nPHASE 4: STACK DEPLOYMENT" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan

Write-Host "Creating CloudFormation stack..." -ForegroundColor Yellow
try {
    $createResult = aws cloudformation create-stack `
        --stack-name $parameters.StackName `
        --template-body file://$($parameters.TemplatePath) `
        --parameters ParameterKey=ImageURI,ParameterValue=$targetImage `
                     ParameterKey=DatabasePassword,ParameterValue=$($parameters.DatabasePassword) `
                     ParameterKey=Environment,ParameterValue=$($parameters.Environment) `
                     ParameterKey=DesiredTaskCount,ParameterValue=$($parameters.DesiredTaskCount) `
        --capabilities CAPABILITY_NAMED_IAM

    $stackId = ($createResult | ConvertFrom-Json).StackId
    Write-Host "Stack creation initiated" -ForegroundColor Green
    Write-Host "Stack ID: $stackId" -ForegroundColor Gray
}
catch {
    Write-Host "ERROR creating stack: $_" -ForegroundColor Red
    exit 1
}

Write-Host "`nPHASE 5: DEPLOYMENT MONITORING" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan

$deploymentSuccess = Monitor-StackDeployment -StackName $parameters.StackName

Write-Host "`nPHASE 6: DEPLOYMENT RESULTS" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan

if ($deploymentSuccess) {
    Write-Host "`nDEPLOYMENT COMPLETED SUCCESSFULLY!" -ForegroundColor Green
    
    try {
        $stackInfo = aws cloudformation describe-stacks --stack-name $parameters.StackName | ConvertFrom-Json
        $outputs = $stackInfo.Stacks[0].Outputs
        
        $vitalinkUrl = ($outputs | Where-Object { $_.OutputKey -eq "VitaLinkURL" }).OutputValue
        $healthCheckUrl = ($outputs | Where-Object { $_.OutputKey -eq "HealthCheckURL" }).OutputValue
        $databaseEndpoint = ($outputs | Where-Object { $_.OutputKey -eq "DatabaseEndpoint" }).OutputValue
        $loadBalancerDNS = ($outputs | Where-Object { $_.OutputKey -eq "LoadBalancerDNS" }).OutputValue
        $vpcId = ($outputs | Where-Object { $_.OutputKey -eq "VPCId" }).OutputValue
        $ecsClusterName = ($outputs | Where-Object { $_.OutputKey -eq "ECSClusterName" }).OutputValue
        
        Write-Host "`nAPPLICATION ENDPOINTS" -ForegroundColor Green
        Write-Host "=================================================" -ForegroundColor Green
        Write-Host "Main URL: $vitalinkUrl" -ForegroundColor White
        Write-Host "Health Check: $healthCheckUrl" -ForegroundColor White
        
        Write-Host "`nINFRASTRUCTURE DETAILS" -ForegroundColor Green
        Write-Host "=================================================" -ForegroundColor Green
        Write-Host "Database Endpoint: $databaseEndpoint" -ForegroundColor White
        Write-Host "Load Balancer: $loadBalancerDNS" -ForegroundColor White
        Write-Host "VPC ID: $vpcId" -ForegroundColor White
        Write-Host "ECS Cluster: $ecsClusterName" -ForegroundColor White
        
        Write-Host "`nHEALTH CHECK VERIFICATION" -ForegroundColor Green
        Write-Host "=================================================" -ForegroundColor Green
        Write-Host "Waiting for application to become healthy..." -ForegroundColor Yellow
        
        $healthCheckSuccess = Test-HealthEndpoint -Url $healthCheckUrl
        
        if ($healthCheckSuccess) {
            Write-Host "`nAPPLICATION IS READY!" -ForegroundColor Green
        }
        else {
            Write-Host "`nManual health check required" -ForegroundColor Yellow
            Write-Host "Check manually: $healthCheckUrl" -ForegroundColor Yellow
        }
        
        Write-Host "`nFINAL SUMMARY" -ForegroundColor Green
        Write-Host "=================================================" -ForegroundColor Green
        Write-Host "Infrastructure deployed successfully" -ForegroundColor Green
        Write-Host "Access your application at:" -ForegroundColor Green
        Write-Host "$vitalinkUrl" -ForegroundColor White
        
        Write-Host "`nUSEFUL COMMANDS" -ForegroundColor Cyan
        Write-Host "=================================================" -ForegroundColor Cyan
        Write-Host "Delete stack when finished:" -ForegroundColor Yellow
        Write-Host "aws cloudformation delete-stack --stack-name $($parameters.StackName)" -ForegroundColor White
        Write-Host "`nCheck stack status:" -ForegroundColor Yellow
        Write-Host "aws cloudformation describe-stacks --stack-name $($parameters.StackName)" -ForegroundColor White
    }
    catch {
        Write-Host "Could not retrieve stack outputs" -ForegroundColor Yellow
    }
}
else {
    Write-Host "`nDEPLOYMENT FAILED!" -ForegroundColor Red
    
    try {
        $events = aws cloudformation describe-stack-events --stack-name $parameters.StackName | ConvertFrom-Json
        $errorEvents = $events.StackEvents | Where-Object { $_.ResourceStatus -like "*FAILED*" } | Select-Object -First 5
        
        if ($errorEvents) {
            Write-Host "`nError details:" -ForegroundColor Red
            foreach ($eventAWS in $errorEvents) {
                Write-Host "Resource: $($eventAWS.LogicalResourceId) ($($eventAWS.ResourceType))" -ForegroundColor Red
                Write-Host "Status: $($eventAWS.ResourceStatus)" -ForegroundColor Red
                Write-Host "Reason: $($eventAWS.ResourceStatusReason)" -ForegroundColor Red
                Write-Host "Timestamp: $($eventAWS.Timestamp)" -ForegroundColor Red
                Write-Host "-----------------------------------------------" -ForegroundColor Red
            }
        }
    }
    catch {
        Write-Host "Could not retrieve error details" -ForegroundColor Red
    }
    exit 1
}

Write-Host "`nMANUAL DEPLOYMENT COMPLETED" -ForegroundColor Green