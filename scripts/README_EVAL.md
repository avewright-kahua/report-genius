Eval Harness

Run the lightweight eval for routing + injection:

```bash
python scripts/eval_agent.py
```

This uses fixtures in `tests/fixtures/docx` and validates:
- intent routing
- token injection success
- idempotency on re-run
