# Script de respaldo automatico a GitHub
# Uso: .\git-backup.ps1 "mensaje del commit"
# Ejemplo: .\git-backup.ps1 "Agregada nueva funcionalidad de reportes"

param(
    [Parameter(Mandatory = $false)]
    [string]$mensaje = "Actualizacion automatica - $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  RESPALDO A GITHUB - EL CANGURO PRO" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar si hay cambios
Write-Host "Verificando cambios..." -ForegroundColor Yellow
$status = git status --porcelain

if ([string]::IsNullOrWhiteSpace($status)) {
    Write-Host "OK - No hay cambios para respaldar" -ForegroundColor Green
    Write-Host ""
    exit 0
}

# Mostrar archivos modificados
Write-Host "Archivos modificados:" -ForegroundColor Yellow
git status --short
Write-Host ""

# Agregar todos los cambios
Write-Host "Agregando archivos..." -ForegroundColor Yellow
git add .

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR - Error al agregar archivos" -ForegroundColor Red
    exit 1
}
Write-Host "OK - Archivos agregados correctamente" -ForegroundColor Green
Write-Host ""

# Hacer commit
Write-Host "Creando commit con mensaje: '$mensaje'" -ForegroundColor Yellow
git commit -m $mensaje

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR - Error al crear commit" -ForegroundColor Red
    exit 1
}
Write-Host "OK - Commit creado correctamente" -ForegroundColor Green
Write-Host ""

# Subir a GitHub
Write-Host "Subiendo cambios a GitHub..." -ForegroundColor Yellow
git push

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR - Error al subir a GitHub" -ForegroundColor Red
    Write-Host "Intenta ejecutar manualmente: git push" -ForegroundColor Yellow
    exit 1
}

Write-Host "OK - Cambios subidos exitosamente a GitHub" -ForegroundColor Green
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  RESPALDO COMPLETADO" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Repositorio: https://github.com/gsmp3ch4m-glitch/plantilla-microcreditos" -ForegroundColor Cyan
Write-Host ""
