$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$privateDir = Join-Path $projectRoot '.local'
New-Item -ItemType Directory -Path $privateDir -Force | Out-Null
foreach ($service in @('bridge', 'tunnel')) {
    $pidPath = Join-Path $privateDir "$service.pid"
    $running = $null
    if (Test-Path -LiteralPath $pidPath) {
        $running = Get-Process -Id ([int](Get-Content -LiteralPath $pidPath)) -ErrorAction SilentlyContinue
        if ($running) {
            $command = (Get-CimInstance Win32_Process -Filter "ProcessId = $($running.Id)").CommandLine
            if (($service -eq 'bridge' -and $command -notmatch 'src.llm_server') -or
                ($service -eq 'tunnel' -and $command -notmatch 'cloudflared')) { $running = $null }
        }
    }
    if (-not $running) {
        if ($service -eq 'bridge') {
            $executable = Join-Path $projectRoot '.venv\Scripts\python.exe'
            $arguments = @('-B', '-m', 'src.llm_server')
        } else {
            $executable = Join-Path $privateDir 'cloudflared.exe'
            $arguments = @('tunnel', '--url', 'http://127.0.0.1:8765', '--no-autoupdate', '--protocol', 'http2')
        }
        $running = Start-Process -FilePath $executable -ArgumentList $arguments -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $privateDir "$service.log") -RedirectStandardError (Join-Path $privateDir "$service-error.log") -PassThru
        $running.Id | Set-Content -LiteralPath $pidPath
    }
}
for ($attempt = 0; $attempt -lt 75; $attempt++) {
    $log = Get-Content -LiteralPath (Join-Path $privateDir 'tunnel-error.log') -Raw -ErrorAction SilentlyContinue
    $url = [regex]::Match([string]$log, 'https://[a-z0-9-]+\.trycloudflare\.com').Value
    $keyPath = Join-Path $privateDir 'llm.key'
    if ($url -and (Test-Path -LiteralPath $keyPath)) { break }
    Start-Sleep -Milliseconds 200
}
if (-not $url) { throw 'Tunnel did not become ready. Check .local/tunnel-error.log.' }
$accessKey = (Get-Content -LiteralPath $keyPath -Raw).Trim()
$settingsPath = Join-Path $privateDir 'streamlit-cloud-secrets.toml'
[System.IO.File]::WriteAllText($settingsPath, "[wattwise_llm]`nurl = `"$url`"`ntoken = `"$accessKey`"`n")
Write-Output 'WattWise AI is running. Keep this PC awake.'
Write-Output "Copy the contents of $settingsPath into your Streamlit app's Secrets settings."
