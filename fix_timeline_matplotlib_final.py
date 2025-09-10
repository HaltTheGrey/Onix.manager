import re

def fix_weekly_timeline_matplotlib():
    """Fix all matplotlib references in weekly_timeline_panel.py"""
    
    with open('chamber_app/ui/weekly_timeline_panel.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix all matplotlib references that weren't caught by the previous script
    fixes = [
        # Direct references that need self.
        (r'(?<!self\.)mdates\.', 'self.mdates.'),
        (r'(?<!self\.)FigureCanvasTkAgg(?!\w)', 'self.FigureCanvasTkAgg'),
        (r'(?<!self\.)Rectangle\(', 'self.Rectangle('),
        
        # Make sure we don't double-fix already fixed references
        (r'self\.self\.', 'self.'),
    ]
    
    for pattern, replacement in fixes:
        content = re.sub(pattern, replacement, content)
    
    with open('chamber_app/ui/weekly_timeline_panel.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Fixed matplotlib references in weekly_timeline_panel.py")

if __name__ == "__main__":
    fix_weekly_timeline_matplotlib()
