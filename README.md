# depwatch

A daemon that monitors dependency files and alerts on outdated or vulnerable packages across multiple repos.

## Installation

```bash
pip install depwatch
```

## Usage

Start the daemon and point it at one or more repositories:

```bash
depwatch start --repos /path/to/repo1 /path/to/repo2
```

depwatch will continuously monitor supported dependency files (`requirements.txt`, `package.json`, `Pipfile`, etc.) and send alerts when packages are outdated or have known vulnerabilities.

### Configuration

Create a `depwatch.yml` in your project root to customize behavior:

```yaml
repos:
  - path: /srv/projects/api
  - path: /srv/projects/frontend

alerts:
  email: team@example.com
  interval: 3600  # check every hour

severity_threshold: medium
```

Then run:

```bash
depwatch start --config depwatch.yml
```

### CLI Commands

| Command | Description |
|---|---|
| `depwatch start` | Start the monitoring daemon |
| `depwatch stop` | Stop the daemon |
| `depwatch status` | Show current daemon status |
| `depwatch scan` | Run a one-time scan and exit |

## Requirements

- Python 3.8+
- Internet access for vulnerability database lookups

## License

This project is licensed under the [MIT License](LICENSE).