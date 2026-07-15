# Support

## How to get help

Use the right channel for the right type of request:

| Need | Best channel |
| --- | --- |
| Usage question or setup help | GitHub Discussions |
| Bug report | GitHub Bug Report issue form |
| Feature idea | GitHub Feature Request issue form |
| Security vulnerability | Private report via [`SECURITY.md`](SECURITY.md) |
| Contributor workflow question | [`CONTRIBUTING.md`](CONTRIBUTING.md) or [`DEVELOPMENT.md`](DEVELOPMENT.md) |
| Documentation gap | Open a docs issue or submit a PR |

## Before opening an issue

- Check [`README.md`](README.md) for quick-start guidance.
- Check [`docs/README.md`](docs/README.md) for the documentation index.
- Check [`TESTING.md`](TESTING.md) and [`docs/TESTING.md`](docs/TESTING.md) if the problem is test-related.
- Search existing issues and discussions first.

## Recommended issue content

Include:

- what you tried,
- expected behavior,
- actual behavior,
- relevant environment details,
- exact error messages or screenshots if available,
- the commit or version you are using.

## Local diagnostic bundle

For runtime problems, open **Admin -> Diagnostics** and review the content-free
state first. Select **Preview bundle**, inspect the exact file inventory, then
confirm **Generate local bundle**. The application writes the archive and its
SHA-256 sidecar locally; it does not upload them.

Maintainers can preview the same contract with:

```powershell
python .\scripts\generate_support_bundle.py --preview
```

Use `--encrypt` when a reviewed bundle must leave the device. The passphrase is
entered interactively. Bundles exclude generic reports and user content, and
re-redact approved logs, but the preview is still mandatory before sharing.

## Security issues

Do **not** open public issues for vulnerabilities. Follow the private reporting instructions in [`SECURITY.md`](SECURITY.md).
