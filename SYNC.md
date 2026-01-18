# Upstream Sync Process

This repository syncs weekly with upstream `zxcalc/pyzx`.

## Manual Sync Steps

1. **Add upstream remote** (if missing):

git remote add upstream https://github.com/zxcalc/pyzx.git

2. **Fetch upstream**:
git fetch upstream

3. **Rebase main onto upstream/main**:
git checkout main
git rebase upstream/main

Resolve conflicts if any.

4. **Force push** (safe):
git push --force-with-lease origin main


## Weekly Routine

1. Run sync above
2. Create sub-issue: "Sync with upstream - Week of [date]"
3. Link to parent issue #X

## GitHub Action (automatic reminder)

See `.github/workflows/sync-reminder.yml`
