#requires -Version 5.1
#requires -RunAsAdministrator

$ErrorActionPreference = 'Stop'
# check command errors ourselves in powershell 7
$PSNativeCommandUseErrorActionPreference = $false

function Invoke-Tool {
    param([string]$Name, [string[]]$Arguments)

    & $Name @Arguments
    if ($LASTEXITCODE -in @(1641, 3010)) {
        throw "$Name requires a Windows restart. Restart Windows and run this script again."
    }
    if ($LASTEXITCODE -ne 0) {
        throw "$Name failed (exit code $LASTEXITCODE). Fix the error above and rerun this script."
    }
}

function Update-SessionPath {
    $env:Path = @(
        [Environment]::GetEnvironmentVariable('Path', 'Machine')
        [Environment]::GetEnvironmentVariable('Path', 'User')
        "$env:LOCALAPPDATA\Microsoft\WinGet\Links"
        "$env:ProgramFiles\Git\cmd"
        "$env:ProgramFiles\Docker\Docker\resources\bin"
        $env:Path
    ) -join ';'
}

function Install-Tool {
    param([string]$Command, [string]$Package, [string[]]$ExtraArguments = @())

    if (Get-Command $Command -ErrorAction SilentlyContinue) { return }

    Write-Host "Installing $Package..."
    & winget install --id $Package --exact --source winget --silent `
        --accept-package-agreements --accept-source-agreements @ExtraArguments | Out-Host
    if ($LASTEXITCODE -in @(1641, 3010)) {
        throw 'Installation requires a restart. Restart Windows and run this script again.'
    }
    if ($LASTEXITCODE -ne 0) {
        throw "WinGet could not install $Package (exit code $LASTEXITCODE)."
    }
    Update-SessionPath
}

# get the repo path from this script
$repoRoot = Split-Path -Parent $PSScriptRoot
$valuesFile = Join-Path $repoRoot 'observability\values.local.yaml'

Write-Host 'Setting up WSL 2 without Ubuntu or another Linux distribution...'
& wsl --install --no-distribution
$wslInstallExit = $LASTEXITCODE
if ($wslInstallExit -notin @(0, 1641, 3010)) {
    throw "WSL installation failed (exit code $wslInstallExit). Fix the error above and rerun."
}
$restartRequired = $wslInstallExit -in @(1641, 3010)
foreach ($featureName in @('VirtualMachinePlatform', 'Microsoft-Windows-Subsystem-Linux')) {
    if ((Get-WindowsOptionalFeature -Online -FeatureName $featureName).State -eq 'EnablePending') {
        $restartRequired = $true
    }
}
if ($restartRequired) {
    Write-Host 'WSL needs a restart. Save your work, then restart Windows and run this script again.'
    if ((Read-Host 'Restart Windows now? [y/N]') -eq 'y') { Restart-Computer }
    return
}
Invoke-Tool -Name wsl -Arguments @('--update') | Out-Host
Invoke-Tool -Name wsl -Arguments @('--set-default-version', '2') | Out-Host

Update-SessionPath
Install-Tool -Command git -Package Git.Git
Write-Host 'Sign in to GitHub in the browser if prompted. Setup continues after sign-in.'
Invoke-Tool -Name git -Arguments @('credential-manager', 'github', 'login', '--browser') | Out-Host

Install-Tool -Command docker -Package Docker.DockerDesktop -ExtraArguments @(
    '--scope', 'machine', '--override',
    'install --quiet --accept-license --backend=wsl-2 --no-windows-containers'
)
Install-Tool -Command minikube -Package Kubernetes.minikube
Install-Tool -Command kubectl -Package Kubernetes.kubectl
Install-Tool -Command helm -Package Helm.Helm

# switch docker to wsl2 while its closed
$dockerSettingsFile = Join-Path $env:APPDATA 'Docker\settings-store.json'
if (Test-Path -LiteralPath $dockerSettingsFile) {
    $dockerSettings = Get-Content -LiteralPath $dockerSettingsFile -Raw | ConvertFrom-Json
    if ($dockerSettings.WslEngineEnabled -ne $true) {
        if (Get-Process -Name 'Docker Desktop' -ErrorAction SilentlyContinue) {
            Invoke-Tool -Name docker -Arguments @('desktop', 'stop', '--timeout', '60') | Out-Host
        }
        # reload settings saved when docker closed
        $dockerSettings = Get-Content -LiteralPath $dockerSettingsFile -Raw | ConvertFrom-Json
        $dockerSettings | Add-Member -NotePropertyName WslEngineEnabled -NotePropertyValue $true -Force
        [IO.File]::WriteAllText($dockerSettingsFile, ($dockerSettings | ConvertTo-Json -Depth 100), [Text.UTF8Encoding]::new($false))
    }
}
Write-Host 'Starting Docker Desktop. Complete its welcome screen if shown; setup waits for the engine.'
Invoke-Tool -Name docker -Arguments @('desktop', 'start', '--timeout', '300') | Out-Host

$previousDockerContext = $env:DOCKER_CONTEXT
$env:DOCKER_CONTEXT = 'desktop-linux'
try {
    $dockerInfo = Invoke-Tool -Name docker -Arguments @('info', '--format', '{{json .}}') | ConvertFrom-Json
    if ($dockerInfo.OSType -ne 'linux' -or $dockerInfo.KernelVersion -notmatch 'microsoft|wsl') {
        throw 'Docker must run Linux containers with its WSL 2 backend. Check the Docker startup error and rerun.'
    }
    minikube start --driver=docker --cpus=2 --memory=4096
    if ($LASTEXITCODE -ne 0) {
        throw 'Minikube failed to start. Fix the error above and rerun this script.'
    }
    Invoke-Tool -Name kubectl -Arguments @('--context=minikube', 'wait', '--for=condition=Ready', 'node/minikube', '--timeout=180s') | Out-Host

    if (-not (Test-Path -LiteralPath $valuesFile)) {
        Write-Host 'OpenObserve password: include at least one uppercase letter, one number, and one punctuation character.'
        Write-Host 'Avoid double quotes and backslashes in credentials; the OpenObserve chart does not escape them.'
        $email = Read-Host 'OpenObserve root email'
        $securePassword = Read-Host 'OpenObserve root password' -AsSecureString
        $credential = [PSCredential]::new($email, $securePassword)
        # json quotes work in yaml too
        $emailYaml = ConvertTo-Json -InputObject $email -Compress
        $passwordYaml = ConvertTo-Json -InputObject ($credential.GetNetworkCredential().Password) -Compress
        $yaml = "auth:`n  ZO_ROOT_USER_EMAIL: $emailYaml`n  ZO_ROOT_USER_PASSWORD: $passwordYaml`n"
        [IO.File]::WriteAllText($valuesFile, $yaml, [Text.UTF8Encoding]::new($false))
        Write-Host 'Created ignored observability/values.local.yaml.'
    } else {
        Write-Host 'Using existing observability/values.local.yaml.'
    }

    Invoke-Tool -Name helm -Arguments @('repo', 'add', 'openobserve', 'https://charts.openobserve.ai', '--force-update') | Out-Host
    Invoke-Tool -Name helm -Arguments @('repo', 'update', 'openobserve') | Out-Host
    Invoke-Tool -Name helm -Arguments @(
        'upgrade', '--install', 'openobserve', 'openobserve/openobserve-standalone',
        '--kube-context', 'minikube', '--namespace', 'stars', '--create-namespace',
        '--values', $valuesFile, '--wait', '--timeout', '10m'
    ) | Out-Host
    Invoke-Tool -Name kubectl -Arguments @('--context=minikube', 'get', 'pods,services', '--namespace=stars') | Out-Host

    Write-Host @'
OpenObserve is ready. Run this command and leave its terminal open:
kubectl --context=minikube --namespace=stars port-forward svc/openobserve-openobserve-standalone 5080:5080
Then open http://localhost:5080 and sign in with your OpenObserve credentials.
'@
} finally {
    $env:DOCKER_CONTEXT = $previousDockerContext
}
