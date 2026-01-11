#!/usr/bin/env python3
"""
CSV Analyzer - Analyzes CSV files for statistics, missing data, and patterns.
A comprehensive data analysis tool for CSV files.
"""

import sys
import csv
from io import StringIO
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Any

def parse_csv(data: str) -> Tuple[List[str], List[Dict[str, str]]]:
    """Parse CSV data and return headers and rows."""
    reader = csv.DictReader(StringIO(data))
    headers = reader.fieldnames or []
    rows = list(reader)
    return headers, rows

def analyze_column(values: List[str], column_name: str) -> Dict[str, Any]:
    """Analyze a single column for statistics."""
    stats = {
        'name': column_name,
        'total': len(values),
        'non_empty': len([v for v in values if v.strip()]),
        'empty': len([v for v in values if not v.strip()]),
    }

    # Try numeric analysis
    numeric_values = []
    for v in values:
        try:
            numeric_values.append(float(v))
        except (ValueError, TypeError):
            pass

    if numeric_values:
        stats['numeric_count'] = len(numeric_values)
        stats['min'] = min(numeric_values)
        stats['max'] = max(numeric_values)
        stats['avg'] = sum(numeric_values) / len(numeric_values)

    # Most common values
    counter = Counter(values)
    stats['most_common'] = counter.most_common(3)
    stats['unique_count'] = len(counter)

    return stats

def analyze_csv(data: str) -> Dict[str, Any]:
    """Analyze CSV data comprehensively."""
    headers, rows = parse_csv(data)

    if not headers or not rows:
        return {'error': 'Invalid CSV data'}

    analysis = {
        'rows': len(rows),
        'columns': len(headers),
        'column_stats': {}
    }

    # Analyze each column
    for header in headers:
        values = [row.get(header, '') for row in rows]
        analysis['column_stats'][header] = analyze_column(values, header)

    return analysis

def format_report(analysis: Dict[str, Any]) -> str:
    """Format analysis results into readable report."""
    if 'error' in analysis:
        return f"Error: {analysis['error']}"

    report = []
    report.append(f"CSV Analysis Report")
    report.append(f"==================")
    report.append(f"Total Rows: {analysis['rows']}")
    report.append(f"Total Columns: {analysis['columns']}")
    report.append("")

    for col_name, stats in analysis['column_stats'].items():
        report.append(f"Column: {col_name}")
        report.append(f"  Total Values: {stats['total']}")
        report.append(f"  Non-Empty: {stats['non_empty']}")
        report.append(f"  Empty: {stats['empty']}")
        report.append(f"  Unique Values: {stats['unique_count']}")

        if 'numeric_count' in stats:
            report.append(f"  Numeric Count: {stats['numeric_count']}")
            report.append(f"  Min: {stats['min']:.2f}")
            report.append(f"  Max: {stats['max']:.2f}")
            report.append(f"  Average: {stats['avg']:.2f}")

        if stats['most_common']:
            report.append(f"  Most Common: {stats['most_common'][0][0]}")

        report.append("")

    return "\n".join(report)

def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: csv_analyzer.py '<csv_data>'")
        sys.exit(1)

    csv_data = sys.argv[1]

    try:
        analysis = analyze_csv(csv_data)
        report = format_report(analysis)
        print(report)
    except Exception as e:
        print(f"Error analyzing CSV: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
