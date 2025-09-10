import re

# Read the file
with open('chamber_app/ui/data_overview_panel.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace matplotlib references with self.attribute
replacements = [
    (r'mdates\.', 'self.mdates.'),
    (r'HourLocator', 'self.HourLocator'),
    (r'DateFormatter', 'self.DateFormatter'),
    (r'plt\.', 'self.plt.'),
    (r'mpatches\.', 'self.mpatches.')
]

for old, new in replacements:
    content = re.sub(old, new, content)

# Write back to file
with open('chamber_app/ui/data_overview_panel.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Updated matplotlib references in data_overview_panel.py')
