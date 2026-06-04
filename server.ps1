# Локальный сервер для игры (без Python)
$port = 8080
$root = $PSScriptRoot
$mime = @{
    '.html' = 'text/html; charset=utf-8'
    '.htm'  = 'text/html; charset=utf-8'
    '.js'   = 'application/javascript'
    '.css'  = 'text/css'
    '.png'  = 'image/png'
    '.jpg'  = 'image/jpeg'
    '.jpeg' = 'image/jpeg'
    '.gif'  = 'image/gif'
    '.webp' = 'image/webp'
    '.mp3'  = 'audio/mpeg'
    '.wav'  = 'audio/wav'
    '.json' = 'application/json'
    '.txt'  = 'text/plain; charset=utf-8'
}

$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add("http://127.0.0.1:${port}/")
$listener.Prefixes.Add("http://localhost:${port}/")

try {
    $listener.Start()
} catch {
    Write-Host "Не удалось занять порт $port. Закройте другой сервер или перезагрузите ПК." -ForegroundColor Red
    Write-Host $_.Exception.Message
    Read-Host "Enter"
    exit 1
}

Write-Host ""
Write-Host "  Сервер запущен!" -ForegroundColor Green
Write-Host "  http://localhost:$port/index.html" -ForegroundColor Cyan
Write-Host "  Папка: $root"
Write-Host "  Ctrl+C — остановить"
Write-Host ""

Start-Process "http://localhost:$port/index.html"

while ($listener.IsListening) {
    $ctx = $listener.GetContext()
    $req = $ctx.Request
    $res = $ctx.Response

    $rel = [Uri]::UnescapeDataString($req.Url.LocalPath).TrimStart('/')
    if ([string]::IsNullOrEmpty($rel)) { $rel = 'index.html' }
    $rel = $rel -replace '/', [IO.Path]::DirectorySeparatorChar
    $file = [IO.Path]::GetFullPath((Join-Path $root $rel))

    if (-not $file.StartsWith($root, [StringComparison]::OrdinalIgnoreCase)) {
        $res.StatusCode = 403
        $buf = [Text.Encoding]::UTF8.GetBytes('403 Forbidden')
        $res.OutputStream.Write($buf, 0, $buf.Length)
        $res.Close()
        continue
    }

    if (Test-Path $file -PathType Leaf) {
        $ext = [IO.Path]::GetExtension($file).ToLower()
        $res.ContentType = $mime[$ext]
        if (-not $res.ContentType) { $res.ContentType = 'application/octet-stream' }
        $bytes = [IO.File]::ReadAllBytes($file)
        $res.ContentLength64 = $bytes.Length
        $res.StatusCode = 200
        $res.OutputStream.Write($bytes, 0, $bytes.Length)
    } else {
        $res.StatusCode = 404
        $msg = "404 Not Found: $($req.Url.LocalPath)"
        $buf = [Text.Encoding]::UTF8.GetBytes($msg)
        $res.ContentLength64 = $buf.Length
        $res.OutputStream.Write($buf, 0, $buf.Length)
    }
    $res.Close()
}
