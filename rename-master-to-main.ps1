param(
    [string]$Root = (Get-Location).Path
)

function Rename-RepoBranch {
    param([string]$RepoPath)

    Write-Host "`n=== $RepoPath ==="
    if (-not (Test-Path (Join-Path $RepoPath '.git'))) {
        Write-Host "  Skipping (no .git folder)"; return
    }

    Push-Location $RepoPath
    try {
        $branchResult = git branch --format="%(refname:short)" 2>$null
        if ($LASTEXITCODE -ne 0) { Write-Host "  git branch failed"; return }

        $branches = $branchResult -split "`n" | ForEach-Object { $_.Trim() } | Where-Object { $_ }
        $hasMaster = $branches -contains 'master'
        $hasMain   = $branches -contains 'main'

        if (-not $hasMaster -and -not $hasMain) {
            Write-Host "  Skipping (neither master nor main)"; return
        }

        if ($hasMaster -and -not $hasMain) {
            Write-Host "  Renaming master -> main"
            git branch -m master main | Out-Null
        }
        elseif ($hasMaster -and $hasMain) {
            Write-Host "  Both master and main exist; leaving as-is"
        }
        else {
            Write-Host "  Already on main"
        }

        $remoteBranches = git branch -r --format="%(refname:short)" 2>$null
        $hasOriginMain = $remoteBranches -contains 'origin/main'

        if (-not $hasOriginMain) {
            Write-Host "  Pushing main to origin"
            git push -u origin main | Out-Null
        } else {
            Write-Host "  Setting upstream to origin/main"
            git branch --set-upstream-to=origin/main main 2>$null | Out-Null
        }

        if ($remoteBranches -contains 'origin/master') {
            Write-Host "  Deleting origin/master"
            git push origin --delete master 2>$null | Out-Null
        } else {
            Write-Host "  origin/master already absent"
        }

        Write-Host "  Updating origin/HEAD"
        git symbolic-ref refs/remotes/origin/HEAD refs/remotes/origin/main 2>$null | Out-Null
        git remote set-head origin --auto 2>$null | Out-Null
    }
    finally { Pop-Location }
}

$gitParentPaths = Get-ChildItem -Path $Root -Recurse -Force |
    Where-Object { $_.Name -eq '.git' } |
    ForEach-Object { $_.Parent.FullName }

if (Test-Path (Join-Path $Root '.git')) {
    $gitParentPaths = @($gitParentPaths + $Root)
}

$gitParentPaths = $gitParentPaths |
    Where-Object { $_ -and (Test-Path $_) } |
    Sort-Object -Unique

foreach ($repoPath in $gitParentPaths) {
    Rename-RepoBranch -RepoPath $repoPath
}
