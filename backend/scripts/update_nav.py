import os
import glob
import re

directory = r"d:\HaryanaSarthi\frontend"
html_files = glob.glob(os.path.join(directory, "*.html"))

for filepath in html_files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if dashboard.html already in nav
    if "dashboard.html" in content and "opportunities.html" in content:
        # Might already be there, let's just make sure we don't duplicate
        continue

    # We want to insert <a href="dashboard.html">Dashboard</a> after opportunities.html
    new_content = re.sub(
        r'(<a href="opportunities\.html"[^>]*>Opportunities</a>)',
        r'\1\n      <a href="dashboard.html">Dashboard</a>',
        content
    )
    
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {os.path.basename(filepath)}")
