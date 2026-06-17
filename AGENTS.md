# Release Surface Scanner

Public-safe release scanner and proof-index package.

Rules:
- Never commit `.env` or `.env.*` files except `.env.example`.
- Do not add secrets, client data, or private operator data.
- Keep fixtures synthetic.
- Run `python -m pytest`, `python scripts/check_public_surface.py`, and `python -m build` before release.
