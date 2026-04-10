# Contributing to KS Data Cloud Collector

Thank you for considering contributing to this project! We welcome contributions from the community.

## How to Contribute

### Reporting Bugs

If you find a bug, please open an issue with:

1. **Clear title** - Describe the issue concisely
2. **Description** - Detailed explanation of the problem
3. **Steps to reproduce** - How to recreate the bug
4. **Expected behavior** - What should happen
5. **Actual behavior** - What actually happens
6. **Environment** - OS, Python version, uv version, etc.
7. **Logs/Screenshots** - If applicable

**Example:**
```
Title: Authentication fails with special characters in password

Description: When the password contains special characters like & or #,
the API authentication fails with a 401 error.

Steps to Reproduce:
1. Set password with & character in .env
2. Run uv run fetch_stations_api.py
3. See authentication error

Expected: Login succeeds
Actual: 401 Unauthorized error

Environment:
- OS: macOS 14.2
- Python: 3.11.5
- uv: 0.1.0
```

### Suggesting Enhancements

For feature requests or enhancements:

1. Check if the feature already exists or is planned
2. Open an issue describing the feature
3. Explain why this feature would be useful
4. Provide examples of how it would work

### Pull Requests

1. **Fork the repository**

   ```bash
   # Fork on GitHub, then clone your fork
   git clone https://github.com/yourusername/ksdatacloud.git
   cd ksdatacloud
   ```

2. **Create a feature branch**

   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/bug-description
   ```

   Use descriptive branch names:
   - `feature/add-csv-export` - For new features
   - `fix/authentication-error` - For bug fixes
   - `docs/improve-readme` - For documentation
   - `refactor/simplify-api-client` - For refactoring

3. **Set up development environment**

   ```bash
   uv sync --dev
   uv run playwright install firefox
   cp .env.example .env
   # Edit .env with test credentials
   ```

4. **Make your changes**

   - Write clear, concise code
   - Follow existing code style
   - Add comments for complex logic
   - Keep functions small and focused

5. **Test your changes**

   ```bash
   # Run the scripts to verify they work
   uv run fetch_stations_api.py --no-stdout
   uv run fetch_stations.py

   # Run linting
   uv run black *.py
   uv run mypy fetch_stations.py fetch_stations_api.py inspect_api_flow.py

   # TODO: Add pytest tests when test suite exists
   # uv run pytest
   ```

6. **Commit your changes**

   ```bash
   git add .
   git commit -m "Add feature: CSV export for station data"
   ```

   **Commit message guidelines:**
   - Use present tense ("Add feature" not "Added feature")
   - Use imperative mood ("Move cursor to..." not "Moves cursor to...")
   - Limit first line to 72 characters
   - Reference issues and pull requests when relevant

   **Examples:**
   ```
   Fix authentication error with special characters

   Escape special characters in password before sending to API.
   Fixes #123
   ```

   ```
   Add CSV export functionality

   - Add --format csv option to fetch_stations_api.py
   - Implement CSV writer for station data
   - Update README with CSV export examples
   ```

7. **Push to your fork**

   ```bash
   git push origin feature/your-feature-name
   ```

8. **Open a Pull Request**

   - Go to the original repository on GitHub
   - Click "New Pull Request"
   - Select your fork and branch
   - Fill in the PR template (if available)
   - Describe your changes clearly
   - Link related issues

## Code Style Guidelines

### Python

- **PEP 8** compliance (enforced by Black)
- **Type hints** for function parameters and return values
- **Docstrings** for classes and functions
- **Line length**: 100 characters (configured in pyproject.toml)

**Example:**

```python
def get_station_info(session: requests.Session, station_id: str) -> dict[str, Any]:
    """
    Retrieve station information from the API.

    Args:
        session: Authenticated requests session
        station_id: Unique station identifier

    Returns:
        Dictionary containing station metadata

    Raises:
        RuntimeError: If API request fails
    """
    response = session.get(
        STATION_INFO_ENDPOINT,
        params={"stationId": station_id},
        timeout=30,
    )
    return unwrap_response(response)
```

### General Principles

- ✅ **DRY** - Don't Repeat Yourself
- ✅ **KISS** - Keep It Simple, Stupid
- ✅ **Single Responsibility** - One function, one purpose
- ✅ **Clear naming** - Variables and functions should explain themselves
- ❌ **No magic numbers** - Use named constants
- ❌ **No hardcoded credentials** - Use environment variables

## Development Workflow

### Before Starting

1. Pull latest changes from main
2. Create a new branch
3. Ensure all tests pass

### While Developing

1. Commit frequently with clear messages
2. Run linting and type checking regularly
3. Test your changes manually
4. Keep commits focused and atomic

### Before Submitting PR

1. Rebase on latest main (if needed)
2. Run all linters and tests
3. Update documentation
4. Verify examples in README still work
5. Check that no credentials are committed

```bash
# Pre-PR checklist
uv run black *.py
uv run mypy fetch_stations.py fetch_stations_api.py inspect_api_flow.py
uv run fetch_stations_api.py --no-stdout  # Verify it works
git log --oneline  # Review commits
git diff main  # Review all changes
```

## Project Structure

When adding new files, follow this structure:

```
ksdatacloud/
├── fetch_*.py              # Data collection scripts
├── tests/                  # Test files
│   └── test_*.py
├── docs/                   # Additional documentation (if needed)
├── examples/               # Example scripts (if needed)
├── .env.example            # Template for credentials
├── pyproject.toml          # Dependencies and config
├── README.md               # Main documentation
├── CHANGELOG.md            # Version history
├── CONTRIBUTING.md         # This file
└── LICENSE                 # License file
```

## Adding New Features

### New Data Collection Method

If adding a new scraping or API method:

1. Create new script: `fetch_stations_<method>.py`
2. Use existing patterns (arg parsing, credential loading)
3. Add error handling and type hints
4. Include usage examples in README
5. Update CHANGELOG.md

### New API Endpoint

If adding support for new KS Data Cloud endpoints:

1. Add endpoint constant at top of file
2. Create dedicated function for the endpoint
3. Document the endpoint in README (API Endpoints section)
4. Handle errors appropriately
5. Add example usage

### New Configuration Option

If adding new settings:

1. Add to `.env.example` with description
2. Update argument parser with new option
3. Document in README (Configuration Options section)
4. Maintain backward compatibility

## Testing

Currently the project uses manual testing. To test your changes:

```bash
# Test API client
uv run fetch_stations_api.py --no-stdout

# Test browser scraper (headful to watch)
uv run fetch_stations.py --headful

# Test network inspector
uv run inspect_api_flow.py

# Test with custom credentials file
uv run fetch_stations_api.py --parameters test_params.txt
```

**Future:** We plan to add pytest-based automated testing.

## Documentation

### Updating README

- Keep examples up to date
- Use consistent formatting
- Test all command examples
- Add troubleshooting for new errors

### Updating CHANGELOG

Follow [Keep a Changelog](https://keepachangelog.com/) format:

```markdown
## [Unreleased]

### Added
- New feature description

### Changed
- Modified behavior description

### Fixed
- Bug fix description

### Security
- Security improvement description
```

## Questions?

If you have questions about contributing:

1. Check existing issues and discussions
2. Open a new issue with "Question:" prefix
3. Contact the maintainers

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Accept constructive criticism
- Focus on what's best for the project
- Show empathy towards others

## Recognition

Contributors will be recognized in:
- Git commit history
- Future CONTRIBUTORS.md file (if created)
- Release notes for significant contributions

Thank you for contributing! 🎉
