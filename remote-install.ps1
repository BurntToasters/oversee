# Installs or updates the oversee skill from GitHub on Windows.
$ErrorActionPreference = 'Stop'
$repo = 'https://github.com/BurntToasters/oversee'
$branch = 'main'
$temp = Join-Path ([IO.Path]::GetTempPath()) ("oversee-" + [Guid]::NewGuid().ToString('N'))

New-Item -ItemType Directory -Path $temp -Force | Out-Null
try {
    $tarball = "$repo/archive/refs/heads/$branch.tar.gz"
    $archive = Join-Path $temp "oversee.tar.gz"
    Write-Host "Fetching the skill from $tarball"
    Invoke-WebRequest -Uri $tarball -OutFile $archive

    $extract = Join-Path $temp "src"
    New-Item -ItemType Directory -Path $extract -Force | Out-Null
    $tar = Get-Command tar -ErrorAction SilentlyContinue
    if ($tar) {
        & tar -xzf $archive -C $extract --strip-components=1
        if ($LASTEXITCODE -ne 0) {
            throw "Archive extraction failed with code $LASTEXITCODE."
        }
    }
    else {
        $zip = Join-Path $temp "oversee.zip"
        Invoke-WebRequest -Uri "$repo/archive/refs/heads/$branch.zip" -OutFile $zip
        Expand-Archive -Path $zip -DestinationPath $extract -Force
        $inner = Get-ChildItem -Path $extract -Directory | Select-Object -First 1
        if ($inner) {
            $extract = $inner.FullName
        }
    }

    if (-not (Test-Path -LiteralPath (Join-Path $extract 'SKILL.md') -PathType Leaf) -or
        -not (Test-Path -LiteralPath (Join-Path $extract 'references/harnesses.md') -PathType Leaf) -or
        -not (Test-Path -LiteralPath (Join-Path $extract 'install.bat') -PathType Leaf)) {
        throw "The downloaded skill payload is incomplete."
    }

    & (Join-Path $extract 'install.bat')
    if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) {
        throw "install.bat exited with code $LASTEXITCODE."
    }
}
finally {
        Remove-Item -LiteralPath $temp -Recurse -Force -ErrorAction SilentlyContinue
}
