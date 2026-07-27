# Repository v1.0 Migration

This package is designed to be extracted into the root of the existing DecisionOS repository.

## Recommended procedure

### Windows PowerShell

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\tools\migrate-repository-v1.ps1
```

### Linux / macOS / Git Bash

```bash
chmod +x tools/migrate-repository-v1.sh
./tools/migrate-repository-v1.sh
```

The scripts move only known existing documents. Other existing directories such as `api`, `database`, `deployment`, `diagrams`, `hardware`, `prompts` and `prototype` are preserved.

After inspection:

```bash
git status
git add -A
git commit -m "chore: establish Repository v1.0 structure"
git push
```
