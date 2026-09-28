## Keeping the GSA-TTS fork in sync with Sartography upstream

We track the Sartography `sartography/spiff-arena` repo as `upstream` and keep our
own long-lived `main`. We **merge** upstream into `main` on a regular cadence
(we do **not** rebase and force-push). Every sync lands through a reviewable
draft PR so we can eyeball incoming changes before they hit `main`.

### The migration complication

The fork carries at least one migration that is **not** upstream
(`8b258f77eafe`, the `task_draft_data` delete / `task_guid` change, joined into
history by the merge-heads migration `1bee6cced5cd`). Because of that, every
time upstream adds a new alembic migration we end up with **multiple alembic
heads**, and `flask db upgrade` will refuse to run until they are reconciled.

We resolve this the same way every time: generate a fresh
`flask db merge heads` migration during the sync and commit it. The sync helper
does this automatically.

### One-command sync (recommended)

```bash
./bin/sync_upstream
```

This will:

1. Fetch `upstream` and `origin`.
2. Cut a dated branch `sync-upstream-YYYY-MM-DD` from `origin/main`.
3. Merge `upstream/main` (stops with clear guidance if there are conflicts).
4. Detect multiple alembic heads and, if present, generate + commit a
   `flask db merge heads` migration.
5. Verify by rebuilding the sqlite schema from migrations (`recreate_db clean`)
   and running `pre-commit`.
6. Push the branch and open a **draft** PR into `main`.

Then: review the PR, wait for CI to go green, and merge it. No force-push.

Flags:

- `--dry-run` — print the plan, change nothing.
- `--no-verify` — skip `recreate_db` + `pre-commit` (faster; not recommended before merge).
- `--no-push` — do everything locally, don't push or open a PR.

Prereqs: an `upstream` remote, a `sartography/sample-process-models` clone next
to `spiff-arena`, and local db deps (mysql-client / mariadb) for the verify step.
Add the remote once with:

```bash
git remote add upstream git@github.com:sartography/spiff-arena.git
```

### Manual fallback

If you need to do it by hand (e.g. a gnarly conflict):

```bash
git fetch upstream --prune
git checkout -b sync-upstream-$(date +%Y-%m-%d) origin/main
git merge upstream/main            # resolve conflicts, prefer keeping BOTH migration chains

cd spiffworkflow-backend
# Only needed when there are multiple heads:
SPIFFWORKFLOW_BACKEND_ENV=local_development SPIFFWORKFLOW_BACKEND_DATABASE_TYPE=sqlite \
  uv run flask db merge heads -m "merging heads from upstream sync"

rm uv.lock
uv sync
SPIFFWORKFLOW_BACKEND_DATABASE_TYPE=sqlite ./bin/recreate_db clean
uv run pre-commit run --all-files   # run again if it reformats anything
cd ..

git add -A && git commit
git push -u origin HEAD
# open a DRAFT PR into main, review, then merge (no force-push)
```
