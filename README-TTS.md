## Updating from the Sartography upstream

1. In your checkout, set an `upstream` remote pointing to Sartography
1. Make a branch at our local main
1. Rebase your branch on top of upstream/main
1. Install dependencies (mysql-client, mariadb)
1. Ensure there's a sartography/sample-process-models clone next to spiff-arena
1. spiffworkflow-backend:
   1. Sync dependencies and recreate the database to apply the upstream
      migrations:

      ```bash
      cd spiffworkflow-backend
      rm uv.lock
      uv sync
      SPIFFWORKFLOW_BACKEND_DATABASE_TYPE=sqlite ./bin/recreate_db clean
      ```

   1. If `recreate_db` fails with
      `Multiple head revisions are present for given argument 'head'`, the
      upstream migrations branched away from ours and the Alembic history now
      has more than one head. Generate a merge migration with the helper
      script, then re-run the recreate:

      ```bash
      ./bin/merge_migration_heads "merging heads"
      SPIFFWORKFLOW_BACKEND_DATABASE_TYPE=sqlite ./bin/recreate_db clean
      ```

      The script adds a new no-op merge migration on top of the current heads
      and prints the result. Commit the generated file in
      `migrations/versions/`.

      > ⚠️ **Never delete or rewrite an existing merge migration.** Older merge
      > revisions may already be stamped in production's `alembic_version`
      > table, so removing or repointing them would break `flask db upgrade` in
      > production. Always resolve head conflicts by layering a _new_ merge
      > migration on top — which is exactly what `bin/merge_migration_heads`
      > does.

   1. Confirm linting and formatting are clean:

      ```bash
      uv run pre-commit  # run again to confirm it got everything; fix any problems
      ```

1. commit changes
1. make a PR that _rebases_ this branch onto `origin/main`
