# Third-Party Notices & Dependency Provenance Register

**AgentGuard Framework** adheres to strict dependency governance. Only permissively licensed, community-standard open-source libraries are used.

Below is the provenance register of direct and development dependencies:

| Dependency | License | Primary Purpose | Provenance / Repository |
| :--- | :--- | :--- | :--- |
| **pyyaml** | MIT | YAML configuration parsing (`scenarios.yaml`, `policy.yaml`) | https://github.com/yaml/pyyaml |
| **jsonschema** | MIT | Validation of evidence receipts and spec schemas | https://github.com/python-jsonschema/jsonschema |
| **pydantic** | MIT | Typed data models and schema generation | https://github.com/pydantic/pydantic |
| **click** | BSD-3-Clause | CLI command interface and argument parsing | https://github.com/pallets/click |
| **jinja2** | BSD-3-Clause | Offline HTML audit report templating | https://github.com/pallets/jinja |
| **pytest** (dev) | MIT | Unit, integration, and offline verification tests | https://github.com/pytest-dev/pytest |
| **black** (dev) | MIT | Code formatting | https://github.com/psf/black |
| **flake8** (dev) | MIT | Static code analysis and linting | https://github.com/pycqa/flake8 |
| **mypy** (dev) | MIT | Static type checking | https://github.com/python/mypy |
| **pre-commit** (dev) | MIT | Pre-commit hook management | https://github.com/pre-commit/pre-commit |

---

## License Texts

All third-party libraries listed above are licensed under standard MIT or BSD licenses. No GPL, AGPL, proprietary, or copyleft dependencies are utilized in the core runtime.
