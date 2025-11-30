<#
SYNOPSIS
  Create .cbz (zip) archives from deepest sub-directories (leaf directories)

DESCRIPTION
  Scans a root path for "deepest" sub-directories that contain files but do
  not have descendant directories that themselves contain files. For each
  such directory it creates a .cbz archive containing the files directly in
  that directory (files only, not parent folder).

USAGE
  .\make-cbz.ps1 -RootPath . -OutputDir .\output

PARAMETERS
  -RootPath  Path to search. Default: current directory.
  -OutputDir Where to write .cbz files. Default: RootPath.
  -IncludeEmpty  If specified, include directories with no files (will create
                 empty zip). Default: false.

NOTES
  Designed for Windows PowerShell 5.1. Uses Compress-Archive. If you prefer
  cross-platform behavior, run the included logic from PowerShell Core or use
  the companion script in another language.
#>

[CmdletBinding()]
param(
    [string]$RootPath = ".",
    [string]$OutputDir = $null,
    [switch]$IncludeEmpty = $false,
    [switch]$DryRun
)

Set-StrictMode -Version Latest

try {
    $rootFull = (Resolve-Path -Path $RootPath).ProviderPath
} catch {
    Write-Error "Root path '$RootPath' not found"
    exit 2
}

# Do not default $OutputDir to root; if not provided we will write each archive
# into the parent directory of the leaf folder. If OutputDir is provided,
# ensure it exists.
if ($OutputDir) {
    if (-not (Test-Path -Path $OutputDir)) {
        New-Item -Path $OutputDir -ItemType Directory | Out-Null
    }
}

# Find all directories under root (including root itself) and treat them as candidates
$allDirs = Get-ChildItem -Path $rootFull -Directory -Recurse -Force -ErrorAction SilentlyContinue
# Also include the root if it contains files directly
$rootDirInfo = Get-Item -LiteralPath $rootFull
$candidates = @()
if ($null -ne $rootDirInfo) { $candidates += $rootDirInfo }
$candidates += $allDirs

$leafDirs = @()
foreach ($d in $candidates) {
    # Files directly in this directory
    $directFiles = Get-ChildItem -Path $d.FullName -File -Force -ErrorAction SilentlyContinue
    if (($directFiles.Count -eq 0) -and (-not $IncludeEmpty)) { continue }

    # Are there any files in descendant directories?
    $descendantFiles = Get-ChildItem -Path $d.FullName -File -Recurse -Force -ErrorAction SilentlyContinue | Where-Object { $_.DirectoryName -ne $d.FullName }
    if ($descendantFiles.Count -eq 0) {
        # this is a deepest sub-directory (no files in child directories)
        $leafDirs += $d
    }
}

if ($leafDirs.Count -eq 0) {
    Write-Host "No leaf directories with files found under '$rootFull'. Nothing to do."
    exit 0
}

foreach ($d in $leafDirs) {
    # Build a safe file name for the archive. Use the directory name, but avoid collisions
    $baseName = $d.Name
    $zipName = "$baseName.cbz"

    # Destination directory: either the provided output directory, or the parent of the leaf
    if ($OutputDir) {
        $destDir = $OutputDir
    } else {
        $destDir = $d.Parent.FullName
    }

    if (-not (Test-Path -Path $destDir)) {
        New-Item -Path $destDir -ItemType Directory | Out-Null
    }

    $destPath = Join-Path -Path $destDir -ChildPath $zipName
    $counter = 1
    while (Test-Path -Path $destPath) {
        $zipName = "{0}_{1}.cbz" -f $baseName, $counter
        $destPath = Join-Path -Path $destDir -ChildPath $zipName
        $counter++
    }

    # Determine files and sizes
    $files = Get-ChildItem -Path $d.FullName -File -Force -ErrorAction SilentlyContinue | Where-Object { -not $_.Name.StartsWith('.') }
    $totalSize = ($files | Measure-Object -Property Length -Sum).Sum

    Write-Host "Creating: $destPath  (from $($d.FullName))"

    if ($PSBoundParameters.ContainsKey('Verbose')) {
        Write-Host "  Files ($($files.Count)) :"
        foreach ($f in $files) { Write-Host "    - $($f.Name) ($([math]::Round($f.Length/1KB,2)) KB)" }
        Write-Host "  Total bytes: $totalSize"
    }

    if ($DryRun) {
        Write-Host "(dry-run) Would create archive: $destPath"
        continue
    }

    # Compress-Archive with path "<dir>\*" will add files at the archive root
    $items = Join-Path -Path $d.FullName -ChildPath '*'
    try {
        Compress-Archive -Path $items -DestinationPath $destPath -Force -ErrorAction Stop
    } catch {
        Write-Warning "Compress-Archive failed for $($d.FullName): $_. Exception.Message"
        continue
    }
}

Write-Host "Done. Created $($leafDirs.Count) .cbz file(s) in '$OutputDir'"
