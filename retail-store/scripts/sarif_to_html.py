#!/usr/bin/env python3
"""
Script to generate an HTML page from a SARIF report (or Trivy JSON report).
Usage: python3 sarif_to_html.py <input_file> [output_file]
If output_file is not provided, outputs to stdout.
"""

import json
import sys
import html
from pathlib import Path

def generate_html(report_data, title="SAST Report"):
    """Generate HTML from the report data."""
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(title)}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        h1 {{
            color: #333;
            text-align: center;
        }}
        .summary {{
            background-color: #e7f3ff;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            text-align: center;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #4CAF50;
            color: white;
            font-weight: bold;
        }}
        tr:nth-child(even) {{
            background-color: #f2f2f2;
        }}
        tr:hover {{
            background-color: #e0e0e0;
        }}
        .severity {{
            font-weight: bold;
            padding: 4px 8px;
            border-radius: 3px;
            color: white;
        }}
        .CRITICAL {{ background-color: #dc3545; }}
        .HIGH {{ background-color: #fd7e14; }}
        .MEDIUM {{ background-color: #ffc107; color: black; }}
        .LOW {{ background-color: #28a745; }}
        .UNKNOWN {{ background-color: #6c757d; }}
        .no-vulnerabilities {{
            text-align: center;
            padding: 20px;
            color: #28a745;
            font-size: 18px;
        }}
    </style>
</head>
<body>
    <h1>{html.escape(title)}</h1>
"""
    # Check if it's SARIF format
    if 'runs' in report_data:
        # SARIF format
        vulnerabilities = []
        for run in report_data.get('runs', []):
            tool_name = run.get('tool', {}).get('driver', {}).get('name', 'Unknown Scanner')
            rules = {rule.get('id'): rule for rule in run.get('tool', {}).get('driver', {}).get('rules', [])}
            for result in run.get('results', []):
                severity = result.get('level')
                if not severity:
                    rule_id = result.get('ruleId')
                    if rule_id and rule_id in rules:
                        severity = rules[rule_id].get('defaultConfiguration', {}).get('level', 'unknown')
                    else:
                        severity = 'unknown'
                # Map SARIF levels to CSS classes
                level_map = {
                    'error': 'HIGH',
                    'warning': 'MEDIUM',
                    'info': 'LOW',
                    'none': 'UNKNOWN'
                }
                severity = level_map.get(severity.lower(), 'UNKNOWN')
                message = result.get('message', {}).get('text', 'N/A')
                location = result.get('locations', [{}])[0].get('physicalLocation', {})
                file_path = location.get('artifactLocation', {}).get('uri', 'N/A')
                start_line = location.get('region', {}).get('startLine', '')
                vuln = {
                    'severity': severity,
                    'name': message,
                    'location': {'file': file_path, 'start_line': start_line},
                    'scanner': {'name': tool_name}
                }
                vulnerabilities.append(vuln)
    else:
        vulnerabilities = report_data.get('vulnerabilities', [])
    
    vuln_count = len(vulnerabilities)

    html_content += f"""
    <div class="summary">
        <h2>Summary</h2>
        <p>Total Vulnerabilities Found: <strong>{vuln_count}</strong></p>
    </div>
"""

    if vuln_count > 0:
        html_content += """
    <table>
        <thead>
            <tr>
                <th>Severity</th>
                <th>Name</th>
                <th>Location</th>
                <th>Scanner</th>
            </tr>
        </thead>
        <tbody>
"""

        for vuln in vulnerabilities:
            severity = vuln.get('severity', 'UNKNOWN').upper()
            name = vuln.get('name') or vuln.get('message', 'N/A')
            location_file = vuln.get('location', {}).get('file', 'N/A')
            start_line = vuln.get('location', {}).get('start_line', '')
            location = f"{location_file}:{start_line}" if start_line else location_file
            scanner = vuln.get('scanner', {}).get('name', 'N/A')

            html_content += f"""
            <tr>
                <td><span class="severity {severity}">{html.escape(severity)}</span></td>
                <td>{html.escape(name)}</td>
                <td>{html.escape(location)}</td>
                <td>{html.escape(scanner)}</td>
            </tr>
"""

        html_content += """
        </tbody>
    </table>
"""
    else:
        html_content += """
    <div class="no-vulnerabilities">
        ✅ No vulnerabilities found!
    </div>
"""

    html_content += """
</body>
</html>
"""

    return html_content

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 sarif_to_html.py <input_file> [output_file]", file=sys.stderr)
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        with open(input_file, 'r') as f:
            report_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in '{input_file}': {e}", file=sys.stderr)
        sys.exit(1)

    title = f"SAST Report - {Path(input_file).stem}"
    html_output = generate_html(report_data, title)

    if output_file:
        with open(output_file, 'w') as f:
            f.write(html_output)
        print(f"HTML report generated: {output_file}")
    else:
        print(html_output)

if __name__ == "__main__":
    main()