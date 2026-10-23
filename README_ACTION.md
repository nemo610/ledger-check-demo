# Nemo CSV JSON Guard

A lightweight GitHub Action that checks CSV structure and JSON syntax inside your CI workflow. It does not upload or persist file contents.

## Use it

```yaml
name: Validate data files
on: [push, pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: nemo610/ledger-check-demo@csv-json-github-action
        with:
          path: .
```

After a versioned release is published, pin the action to a release tag (for example `@v1`) instead of a branch.

## Inputs

- `path`: file or directory to inspect; directories are scanned recursively for `.csv` and `.json` files. Default: `.`.
- `fail_on_empty_csv`: set to `true` to reject CSVs that have a header but no data rows. Default: `false`.

## Checks

- CSV can be parsed as UTF-8, with or without a BOM.
- CSV header is present, non-empty, and has no duplicate or blank column names.
- Each CSV data row has the same number of fields as the header.
- JSON files parse successfully.
- Hidden runtime directories such as `.git`, virtual environments, and `node_modules` are skipped.

This is a structural validator, not a schema validator: it does not verify business rules or whether values are semantically correct.

## Privacy

Validation runs on the GitHub Actions runner. The script prints file paths and validation errors, not file contents. Do not commit secrets or sensitive data to a repository.

## Limitations

The action requires Python 3 on the runner and is intended for Linux runners. It is provided as-is; test it against your own fixtures before relying on it for production pipelines.
