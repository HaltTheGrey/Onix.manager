import re

# Read the file
with open('chamber_app/ui/weekly_timeline_panel.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace matplotlib references with self.attribute
replacements = [
    (r'plt\.', 'self.plt.'),
    (r'mdates\.', 'self.mdates.'),
    (r'FigureCanvasTkAgg', 'self.FigureCanvasTkAgg'),
    (r'Rectangle\(', 'self.Rectangle(')
]

for old, new in replacements:
    content = re.sub(old, new, content)

# Write back to file
with open('chamber_app/ui/weekly_timeline_panel.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Updated matplotlib references in weekly_timeline_panel.py')
