# Task app team conventions (from the taskapp-tools kit)

- Start every task on its own branch named feat/<short-name>. Never commit to main.
- Standard library only. Don't add third-party packages.
- Before you commit, run both of these and fix anything they report:
  - `ruff check .`
  - `python3 -m unittest`
- The only external API this project uses is the Nager.Date public holiday API
  at date.nager.at. This kit already allows it. Don't call any other external service.
- Tests must never make real network calls. Stub external requests.
