import os
import pandas as pd
import glob
import re
import json
import argparse
from datetime import datetime
from jinja2 import Template

# HTML Template for individual stats pages
STATS_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>{{ title }} - Legislative Acts Statistics</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }
        .container { max-width: 1200px; margin: 0 auto; }
        table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        h1, h2, h3 { color: #333; }
        .summary { background-color: #f0f8ff; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
        .back-link { margin-bottom: 20px; }
        .citation { background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin-top: 20px; }
        .citation pre { overflow-x: auto; background: #eee; padding: 10px; border-radius: 3px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="back-link">
            <a href="../index.html">← Back to main page</a>
        </div>
        
        <h1>{{ title }}</h1>
        <p>Data for: {{ period }}</p>
        
        {% if doi_info %}
        <div class="citation">
            <h2>Citation Information</h2>
            <p><strong>DOI:</strong> <a href="https://doi.org/{{ doi_info.doi }}" target="_blank">{{ doi_info.doi }}</a></p>
            
            <h3>APA Format</h3>
            <p>{{ doi_info.apa }}</p>
            
            <h3>MLA Format</h3>
            <p>{{ doi_info.mla }}</p>
            
            <h3>BibTeX</h3>
            <pre>{{ doi_info.bibtex }}</pre>
        </div>
        {% endif %}
        
        <div class="summary">
            <h2>Summary Statistics</h2>
            <p>Total number of acts: {{ total_acts }}</p>
            <p>Basic acts: {{ basic_acts }}</p>
            <p>Amending acts: {{ amending_acts }}</p>
        </div>
        
        <h2>Statistics by Year</h2>
        <table>
            <tr>
                <th>Year</th>
                <th>Basic Acts</th>
                <th>Amending Acts</th>
                <th>Total</th>
            </tr>
            {% for year, data in yearly_stats.items() %}
            <tr>
                <td>{{ year }}</td>
                <td>{{ data['basic'] }}</td>
                <td>{{ data['amending'] }}</td>
                <td>{{ data['total'] }}</td>
            </tr>
            {% endfor %}
        </table>
        
        <h2>Statistics by Category</h2>
        <table>
            <tr>
                <th>Category</th>
                <th>Basic Acts</th>
                <th>Amending Acts</th>
                <th>Total</th>
            </tr>
            {% for category, data in category_stats.items() %}
            <tr>
                <td>{{ category }}</td>
                <td>{{ data['basic'] }}</td>
                <td>{{ data['amending'] }}</td>
                <td>{{ data['total'] }}</td>
            </tr>
            {% endfor %}
        </table>
        
        <h2>Detailed Statistics</h2>
        <table>
            <tr>
                <th>Category</th>
                <th>Act Type</th>
                <th>Basic</th>
                <th>Amending</th>
                <th>Total</th>
            </tr>
            {% for category, types in detailed_stats.items() %}
                {% for act_type, counts in types.items() %}
                <tr>
                    <td>{{ category }}</td>
                    <td>{{ act_type }}</td>
                    <td>{{ counts['basic'] }}</td>
                    <td>{{ counts['amending'] }}</td>
                    <td>{{ counts['total'] }}</td>
                </tr>
                {% endfor %}
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""

# HTML Template for the index page
INDEX_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Legislative Acts Data</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 0; line-height: 1.6; }
        .container { display: flex; height: 100vh; }
        .sidebar { width: 250px; background-color: #f8f9fa; padding: 20px; overflow-y: auto; }
        .main-content { flex-grow: 1; padding: 20px; overflow-y: auto; }
        .sidebar h2 { margin-top: 0; }
        .sidebar ul { padding-left: 0; list-style-type: none; }
        .sidebar li { margin-bottom: 8px; }
        .sidebar a { text-decoration: none; color: #007bff; }
        .sidebar a:hover { text-decoration: underline; }
        .current { font-weight: bold; }
        iframe { width: 100%; height: 100%; border: none; }
        .doi-link { font-size: 0.9em; margin-left: 5px; text-decoration: none; color: #0366d6; }
        .doi-link:hover { text-decoration: underline; }
        .doi-badge { display: inline-block; font-size: 0.8em; background: #f1f8ff; padding: 1px 6px; 
                    border-radius: 3px; border: 1px solid #c8e1ff; color: #0366d6; margin-left: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="sidebar">
            <h2>Legislative Acts Statistics</h2>
            <p>Monthly statistics of EU legislative acts.</p>
            <h3>Available Reports</h3>
            <ul id="stats-list">
                {% for file in stats_files %}
                <li>
                    <a href="#{{ file.id }}" class="stats-link