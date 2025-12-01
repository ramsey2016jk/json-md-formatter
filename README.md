# JSON & Markdown Formatter / Validator

**JSON & Markdown Formatter / Validator** is a small Python CLI tool to validate and format JSON and Markdown files. It helps detect common JSON mistakes, pretty-print JSON, normalize Markdown headings, and validate/format simple Markdown tables.

## Features
- Validate JSON files and report errors with line/column.
- Attempt to auto-detect and fix common JSON mistakes (trailing commas, single quotes).
- Pretty-print JSON with consistent indentation.
- Normalize Markdown heading levels (`#`, `##`, `###`) and ensure consistent spacing.
- Validate simple Markdown tables and reformat them with aligned columns.
- CLI interface for quick validation/formatting.

## Installation
This project uses only Python standard libraries (tested with Python 3.8+).

1. Clone or download the repository.
2. (Optional) Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # macOS / Linux
   .venv\Scripts\activate    # Windows
   ```
3. Install dependencies (none required):
   ```bash
   pip install -r requirements.txt
   ```

## Usage
Run the main script `formatter.py` with one of the CLI flags:

```
# Validate JSON (reports errors)
python formatter.py --validate-json sample.json

# Format JSON (pretty-print). Optional: --out to save output
python formatter.py --format-json sample.json --out formatted.json

# Validate Markdown
python formatter.py --validate-md sample.md

# Format Markdown (normalize headings + format tables). Optional: --out to save output
python formatter.py --format-md sample.md --out formatted.md
```

## Examples

### Example messy JSON (in `sample.json`)
```json
{
  "name": "Sample",
  "items": [1,2,3,],
  "note": 'This uses single quotes',
}
```

### After formatting
```json
{
  "name": "Sample",
  "items": [
    1,
    2,
    3
  ],
  "note": "This uses single quotes"
}
```

### Example messy Markdown (in `sample.md`)
```
#Title
Some intro text
##  Subheading
| Name|Age|
|--|--|
|Alice|30|
|Bob| 25|
```

### After formatting
```
# Title

Some intro text

## Subheading

| Name  | Age |
|-------|-----|
| Alice | 30  |
| Bob   | 25  |
```

## Files
- `formatter.py` — main script
- `sample.json` — messy JSON for testing
- `sample.md` — messy Markdown for testing
- `requirements.txt` — dependencies (none)

## License
MIT
