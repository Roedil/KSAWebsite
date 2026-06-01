# Production server for Windows (waitress).
# Run:  .\serve.ps1        -> serves on http://0.0.0.0:5055
$port = if ($env:PORT) { $env:PORT } else { "5055" }
Write-Host "Starting KSA Metrology site on 0.0.0.0:$port (waitress)..."
waitress-serve --host=0.0.0.0 --port=$port wsgi:app
