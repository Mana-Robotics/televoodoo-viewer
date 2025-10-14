### Installing voodoo_core into a venv

From the repo root:

```bash
cd /Users/daniel/Code/mana/voodoo-control/VoodooControlDesktop
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
pip install -e python
```

Now `voodoo_core` is importable in the venv without manually setting PYTHONPATH.


