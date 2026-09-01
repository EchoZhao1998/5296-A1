#!/usr/bin/env python3
"""Check that a run of Group001_solution.ipynb reproduced the agreed output.

    python3 Group001_verify.py [path/to/outputs]

Compares every file in the folder against Group001_outputs.sha256, which sits beside this
script. Not part of the submission — it exists so "I ran it" can be checked rather than
assumed, and so a stale copy of the six CSVs cannot be mistaken for a fresh one.
"""
import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / 'Group001_outputs.sha256'


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as fh:
        for block in iter(lambda: fh.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def main():
    if len(sys.argv) > 1:
        folder = Path(sys.argv[1])
    else:
        folder = next((p for p in [Path('outputs'), Path('.'), Path('../outputs'),
                                   HERE.parent / 'outputs']
                       if (p / 'Group001_orders_standardised.csv').exists()), None)
    if folder is None or not folder.is_dir():
        sys.exit('No outputs folder found. Pass one: python3 Group001_verify.py path/to/outputs')

    expected = {}
    for line in MANIFEST.read_text().splitlines():
        want, name = line.split(maxsplit=1)
        expected[name.strip()] = want

    print(f'checking {folder.resolve()}\n')
    same = differ = missing = 0
    for name, want in sorted(expected.items()):
        path = folder / name
        if not path.exists():
            print(f'  MISSING  {name}')
            missing += 1
            continue
        got = digest(path)
        if got == want:
            print(f'  match    {name}')
            same += 1
        else:
            print(f'  DIFFERS  {name}')
            print(f'           expected {want[:16]}...  got {got[:16]}...')
            differ += 1

    print(f'\n{same} match, {differ} differ, {missing} missing, of {len(expected)} files')
    if differ or missing:
        print('\nA difference means this run did not reproduce the agreed output. Most likely')
        print('causes, in order: an older Group001_text_functions.py beside the notebook, a')
        print('different allocated package, or a partial run. Say so in the group chat rather')
        print('than building figures on it.')
        return 1
    print('\nThis run reproduced the agreed output exactly. Your own outputs/ folder is now')
    print('redundant - build the EDA against the shared copy so all eight figures agree.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
