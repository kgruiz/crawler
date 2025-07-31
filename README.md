<p align="center">
  <img src="icon.png" alt="Stealth Crawler Icon" width="200">
</p>

<h1 align="center">Stealth Crawler</h1>

<p align="center">
A headless-Chrome web crawler that discovers same-host links and optionally saves HTML, Markdown, PDF, or screenshots. Use as a library or via the <code>stealth-crawler</code> CLI.
</p>

<p align="center">
  <a href="https://pypi.org/project/stealth-crawler/">
    <img src="https://img.shields.io/pypi/v/stealth-crawler.svg" alt="PyPI">
  </a>&nbsp;&nbsp;
  <a href="https://github.com/kgruiz/stealth-crawler/blob/main/LICENSE">
    <img src="https://img.shields.io/pypi/l/stealth-crawler.svg" alt="License">
  </a>
</p>

---

## Features

- Asynchronous, headless Chrome browsing via `pydoll`
- Discovers internal links starting from a root URL
- Optional content saving:
  - HTML
  - Markdown (via `html2text`)
  - PDF snapshots
  - PNG screenshots
- Rich progress bars with `rich`
- Configurable URL filtering (base, exclude)
- Pure-Python API and CLI

---

## Installation

Install the latest stable release:

```bash
pip install stealth-crawler
```

Or in isolation:

```bash
pipx install stealth-crawler
```

Or via other tools:

* **uv**

  ```bash
  uv venv .venv
  source .venv/bin/activate
  uv pip install stealth-crawler
  ```

* **Poetry**

  ```bash
  poetry add stealth-crawler
  ```

---

## Quickstart

### <img src="https://upload.wikimedia.org/wikipedia/commons/b/b3/Terminalicon2.png" alt="Terminal" width="30" style="vertical-align: middle;" /> Command-Line

```bash
# Discover URLs only
stealth-crawler crawl https://example.com --urls-only

# Crawl and save HTML + Markdown
stealth-crawler crawl https://example.com \
  --save-html --save-md \
  --output-dir ./output

# Exclude specific paths
stealth-crawler crawl https://example.com \
  --exclude /private,/logout
```

Run `stealth-crawler --help` for full options.

### <img src="https://s3.dualstack.us-east-2.amazonaws.com/pythondotorg-assets/media/files/python-logo-only.svg" alt="Python" width="30" style="vertical-align: middle;" /> Python API

```python
import asyncio
from stealthcrawler import StealthCrawler

crawler = StealthCrawler(
    base="https://example.com",
    exclude=["/admin"],
    save_html=True,
    save_md=True,
    output_dir="export"
)
urls = asyncio.run(crawler.crawl("https://example.com"))
print(urls)
```

---

## Configuration

| Option        | CLI flag       | API param    | Default    |
| ------------- | -------------- | ------------ | ---------- |
| Base URL(s)   | `--base`       | `base`       | start URL  |
| Exclude paths | `--exclude`    | `exclude`    | none       |
| Save HTML     | `--save-html`  | `save_html`  | `False`    |
| Save Markdown | `--save-md`    | `save_md`    | `False`    |
| URLs only     | `--urls-only`  | `urls_only`  | `False`    |
| Output folder | `--output-dir` | `output_dir` | `./output` |

---

## Testing & Quality

* Run tests:

  ```bash
  pytest
  ```

* Check formatting & linting:

  ```bash
  black src tests
  ruff check src tests
  ```

---

## Contributing

1. Fork the repository and create a feature branch.
2. Set up your development environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]"
   ```

   Or with **uv**:

   ```bash
   uv venv .venv
   source .venv/bin/activate
   uv pip install -e ".[dev]"
   ```
3. Implement your changes, add tests, and run:

   ```bash
   black src tests
   ruff check src tests
   pytest
   ```
4. Open a pull request against `main`.

---

## License

This project is licensed under the **GNU General Public License v3.0 or later** (GPL-3.0-or-later).
You are free to use, modify, and redistribute under the terms of the GPL.
See [LICENSE](./LICENSE) for full details.