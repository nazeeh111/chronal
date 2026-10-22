# Contributing

Use Python 3.11 or newer. Install with `python -m pip install -e '.[dev]'` and run:

```sh
ruff check chronal tests tools
ruff format --check chronal tests tools
python -m unittest discover -s tests -v
python -m chronal demo --out demo-run
python -m chronal verify demo-run --replay
```

Use a fresh output folder for each experiment. Never update a published example by editing its metrics or resealing changed data. Regenerate it from the current source and retain its recipe.

Financial changes need an independently derived small ledger or formula check, and tests at the affected timing boundary. Add future-suffix perturbation tests for new features, models, risk decisions and memory. Preserve cash continuity across model refits. Treat a model-generated proposal as untrusted input; no arbitrary Python, shell, imports or network access belongs in the proposal contract.

Keep the default installation small. A new dependency should solve a problem the current scope actually has. An adapter needs an executable conformance example before documentation calls it supported. Respect each upstream license and keep data rights separate from code rights. Prefer extension through existing modules over another framework layer.

The generated reports use plain HTML, CSS, SVG and JavaScript. Keep them standalone, keyboard usable, free of external assets, and explicit about synthetic data and observed holdouts. Include a visual check for substantial presentation changes.

Do not add a live brokerage route as a convenience flag. Live execution would require a separate product scope, authorization, venue-specific accounting and operational controls.
