# Contributing to LAUT

LAUT welcomes scientific, data-engineering, documentation, and regional-process
contributions.

## Development setup

```console
python -m venv .venv
source .venv/bin/activate
pip install -e '.[ocean,test]'
pytest
```

## Scientific changes

Threshold or ranking changes require:

1. a new framework version;
2. the evaluation period, masks, references, and data versions;
3. evidence from the existing hindcast and/or literature;
4. a migration note describing changed acceptance decisions; and
5. scientific review by a regional ocean modeller.

Do not change a released framework file in place.

## Code changes

- Add focused tests with finite values, missing values, and boundary cases.
- Keep metrics pure and return one documented scalar.
- Keep provider credentials and large data out of git.
- Preserve the distinction between target, threshold, missing, and not
  applicable.
- Run `pytest` and `python -m laut validate-framework` before opening a pull
  request.

## Reporting issues

Include the LAUT version, framework version, run stage, source types, criterion
ID, expected/actual result, and a minimal synthetic reproduction where possible.

