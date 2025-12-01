#!/usr/bin/env python3
"""
formatter.py

JSON & Markdown Validator / Formatter

CLI:
    --validate-json file.json
    --format-json file.json
    --validate-md file.md
    --format-md file.md

Optional:
    --out OUTPUT_FILE   (for format operations, to save output)
"""

import argparse
import json
import re
import sys
from typing import Tuple, List

def detect_json_errors(text: str) -> Tuple[bool, str]:
    try:
        json.loads(text)
        return True, 'Valid JSON'
    except json.JSONDecodeError as e:
        return False, f"JSONDecodeError: {e.msg} (line {e.lineno} column {e.colno})"

def try_repair_json(text: str) -> str:
    original = text
    text = re.sub(r'//.*', '', text)
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    text = re.sub(r',\s*(\}|])', r'\1', text)
    def _replace_single_quotes(match):
        inner = match.group(1)
        inner_escaped = inner.replace('"', '\\"')
        return '"' + inner_escaped + '"'
    text = re.sub(r"'([^'\\]*(?:\\.[^'\\]*)*)'", _replace_single_quotes, text)
    text = re.sub(r',\s*([}\]])', r'\1', text)
    return text if text.strip() else original

def validate_json_file(path: str) -> int:
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    ok, msg = detect_json_errors(text)
    if ok:
        print(f"[OK] {path}: {msg}")
        return 0
    else:
        print(f"[ERR] {path}: {msg}")
        repaired = try_repair_json(text)
        if repaired != text:
            print('\n[HINT] Suggested repaired JSON (preview):\n')
            try:
                parsed = json.loads(repaired)
                preview = json.dumps(parsed, indent=2, ensure_ascii=False)
                print(preview)
            except Exception:
                print('  (auto-repair failed to produce valid JSON)')
        return 1

def format_json_file(path: str, out: str = None) -> int:
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    try:
        obj = json.loads(text)
    except json.JSONDecodeError as e:
        print(f"[ERR] Cannot format: JSON invalid - {e.msg} (line {e.lineno} column {e.colno})")
        repaired = try_repair_json(text)
        try:
            obj = json.loads(repaired)
            print("[INFO] Auto-repair succeeded; formatting repaired JSON.")
        except Exception:
            print("[ERR] Auto-repair failed; aborting format.")
            return 1
    pretty = json.dumps(obj, indent=2, ensure_ascii=False)
    if out:
        with open(out, 'w', encoding='utf-8') as f:
            f.write(pretty + "\n")
        print(f"[OK] Formatted JSON saved to {out}")
    else:
        print(pretty)
    return 0

# -------------------------
# Markdown processing
# -------------------------
def normalize_heading(line: str) -> str:
    m = re.match(r'^(#{1,6})\s*(.*)$', line)
    if m:
        hashes = m.group(1)
        text = m.group(2).strip()
        return f"{hashes} {text}"
    m2 = re.match(r'^(#{1,6})([^\s#].*)$', line)
    if m2:
        hashes = m2.group(1)
        text = m2.group(2).strip()
        return f"{hashes} {text}"
    return line

def find_tables(lines: List[str]) -> List[tuple]:
    ranges = []
    i = 0
    n = len(lines)
    while i < n - 1:
        if '|' in lines[i]:
            j = i + 1
            if '|' in lines[j] and re.search(r':?-{3,}:?', lines[j]):
                k = j + 1
                while k < n and ('|' in lines[k] and lines[k].strip() != ''):
                    k += 1
                ranges.append((i, k))
                i = k
                continue
        i += 1
    return ranges

def parse_table_block(block: List[str]):
    if len(block) < 2:
        return [], None
    header = block[0].strip()
    sep = block[1].strip()
    rows = []
    def split_row(r):
        parts = [c.strip() for c in r.strip().strip('|').split('|')]
        return parts
    rows.append(split_row(header))
    for r in block[2:]:
        rows.append(split_row(r))
    return rows, sep

def validate_table(rows: List[List[str]], sep_line: str):
    if not rows:
        return False, 'Empty table'
    ncols = len(rows[0])
    for idx, r in enumerate(rows):
        if len(r) != ncols:
            return False, f'Row {idx+1} has {len(r)} columns; expected {ncols}'
    parts = [p.strip() for p in sep_line.strip().strip('|').split('|')]
    if len(parts) != ncols:
        return False, f'Separator has {len(parts)} columns; expected {ncols}'
    for p in parts:
        if not re.match(r'^:?-{3,}:?$', p):
            return False, f"Separator segment '{p}' is not a valid alignment marker (--- or :---:)"
    return True, 'Table looks valid'

def format_table(rows: List[List[str]]) -> str:
    if not rows:
        return ''
    ncols = len(rows[0])
    widths = [0]*ncols
    for r in rows:
        for i, c in enumerate(r):
            widths[i] = max(widths[i], len(c))
    header = '| ' + ' | '.join(r.ljust(widths[i]) for i, r in enumerate(rows[0])) + ' |'
    sep = '| ' + ' | '.join('-' * max(3, widths[i]) for i in range(ncols)) + ' |'
    body_lines = []
    for r in rows[1:]:
        line = '| ' + ' | '.join(r.ljust(widths[i]) for i, r in enumerate(r)) + ' |'
        body_lines.append(line)
    return '\n'.join([header, sep] + body_lines)

def validate_md_file(path: str) -> int:
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    problems = []
    table_ranges = find_tables(lines)
    for start, end in table_ranges:
        block = [l.rstrip('\n') for l in lines[start:end]]
        rows, sep = parse_table_block(block)
        ok, msg = validate_table(rows, sep)
        if not ok:
            problems.append(f'Table at lines {start+1}-{end} : {msg}')
    if problems:
        print('[ERR] Markdown validation found issues:')
        for p in problems:
            print('  -', p)
        return 1
    print('[OK] No table structure issues found in', path)
    return 0

def format_md_file(path: str, out: str = None) -> int:
    with open(path, 'r', encoding='utf-8') as f:
        raw = f.read()
    lines = raw.splitlines()
    new_lines = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        line = normalize_heading(line)
        if re.match(r'^#{1,6}\s', line):
            new_lines.append(line.strip())
            if i+1 < n and lines[i+1].strip() != "":
                new_lines.append("")
            i += 1
            continue
        new_lines.append(line.rstrip())
        i += 1
    out_lines = []
    i = 0
    n = len(new_lines)
    while i < n:
        line = new_lines[i]
        if '|' in line and i+1 < n and '|' in new_lines[i+1] and re.search(r':?-{3,}:?', new_lines[i+1]):
            block = []
            j = i
            while j < n and '|' in new_lines[j] and new_lines[j].strip() != "":
                block.append(new_lines[j])
                j += 1
            rows, sep = parse_table_block(block)
            ok, msg = validate_table(rows, sep)
            if not ok:
                out_lines.extend(block)
            else:
                formatted = format_table(rows)
                out_lines.extend(formatted.splitlines())
            i = j
            continue
        out_lines.append(line)
        i += 1
    final_text = '\n'.join(out_lines).rstrip() + '\n'
    if out:
        with open(out, 'w', encoding='utf-8') as f:
            f.write(final_text)
        print(f"[OK] Formatted Markdown saved to {out}")
    else:
        print(final_text)
    return 0

def main():
    parser = argparse.ArgumentParser(description='JSON & Markdown Formatter / Validator')
    parser.add_argument('--validate-json', help='Validate JSON file path')
    parser.add_argument('--format-json', help='Format JSON file path')
    parser.add_argument('--validate-md', help='Validate Markdown file path')
    parser.add_argument('--format-md', help='Format Markdown file path')
    parser.add_argument('--out', help='Optional output path for format commands')
    args = parser.parse_args()

    if args.validate_json:
        sys.exit(validate_json_file(args.validate_json))
    if args.format_json:
        sys.exit(format_json_file(args.format_json, args.out))
    if args.validate_md:
        sys.exit(validate_md_file(args.validate_md))
    if args.format_md:
        sys.exit(format_md_file(args.format_md, args.out))

    parser.print_help()
    sys.exit(0)

if __name__ == '__main__':
    main()
