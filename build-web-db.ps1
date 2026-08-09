[CmdletBinding()]
param(
    [string]$CorpusPath = "Index\lib\x86_64-win64",
    [string]$DbPath = "web\corpus.db"
)

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$resolvedCorpusPath = Join-Path $repoRoot $CorpusPath
$resolvedDbPath = Join-Path $repoRoot $DbPath
$ingestScript = Join-Path $repoRoot "web\ingest\ingest.py"

if (-not (Test-Path -LiteralPath $ingestScript)) {
    throw "Ingest script not found: $ingestScript"
}

if (-not (Test-Path -LiteralPath $resolvedCorpusPath)) {
    throw "Corpus path not found: $resolvedCorpusPath"
}

$dbParent = Split-Path -Parent $resolvedDbPath
if (-not (Test-Path -LiteralPath $dbParent)) {
    New-Item -ItemType Directory -Path $dbParent | Out-Null
}

Write-Host "Building web corpus database..."
Write-Host "Corpus: $resolvedCorpusPath"
Write-Host "Database: $resolvedDbPath"

# H2433 - run any configured headless Corpus_builder jobs before ingest.
# No jobs file / SKIP_HEADLESS_CB=1 -> no-op (prebuilt HTML unaffected).
$headlessScript = Join-Path $repoRoot "scripts\run_headless_cb.py"
python $headlessScript --repo-root $repoRoot --corpus-path $resolvedCorpusPath
if ($LASTEXITCODE -ne 0) {
    throw "Headless corpus-builder step failed with exit code $LASTEXITCODE."
}

python $ingestScript --corpus-path $resolvedCorpusPath --db-path $resolvedDbPath
if ($LASTEXITCODE -ne 0) {
    throw "Database build failed with exit code $LASTEXITCODE."
}

Write-Host "Database build complete."

