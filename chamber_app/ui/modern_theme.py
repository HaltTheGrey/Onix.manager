"""
Modern UI Theme Configuration
Comprehensive theming system for a professional, modern appearance
"""

import customtkinter as ctk
from typing import Dict, Any, Optional, Union, Tuple
import json
import os

class ModernThemeManager:
    """Advanced theme manager for modern UI styling"""
    
    def __init__(self):
        self.themes = {
            "modern_dark": {
                "name": "Modern Dark",
                "appearance_mode": "dark",
                "color_theme": "blue",
                "colors": {
                    # Primary colors
                    "primary": "#1e88e5",
                    "primary_dark": "#1565c0", 
                    "primary_light": "#42a5f5",
                    
                    # Accent colors
                    "accent": "#ff6b35",
                    "accent_dark": "#e64100",
                    "accent_light": "#ff8a65",
                    
                    # Success/Warning/Error
                    "success": "#4caf50",
                    "warning": "#ff9800", 
                    "error": "#f44336",
                    "info": "#2196f3",
                    
                    # Backgrounds
                    "bg_primary": "#121212",
                    "bg_secondary": "#1e1e1e",
                    "bg_tertiary": "#2d2d2d",
                    "bg_card": "#252525",
                    
                    # Text
                    "text_primary": "#ffffff",
                    "text_secondary": "#e0e0e0",
                    "text_muted": "#9e9e9e",
                    
                    # Borders
                    "border": "#404040",
                    "border_light": "#505050",
                    "border_accent": "#1e88e5",
                    
                    # Status indicators
                    "status_online": "#4caf50",
                    "status_offline": "#f44336",
                    "status_maintenance": "#ff9800",
                    "status_idle": "#9e9e9e",
                }
            },
            "modern_light": {
                "name": "Modern Light",
                "appearance_mode": "light", 
                "color_theme": "blue",
                "colors": {
                    # Primary colors
                    "primary": "#1976d2",
                    "primary_dark": "#1565c0",
                    "primary_light": "#42a5f5",
                    
                    # Accent colors
                    "accent": "#ff5722",
                    "accent_dark": "#e64100", 
                    "accent_light": "#ff8a65",
                    
                    # Success/Warning/Error
                    "success": "#388e3c",
                    "warning": "#f57c00",
                    "error": "#d32f2f", 
                    "info": "#1976d2",
                    
                    # Backgrounds
                    "bg_primary": "#fafafa",
                    "bg_secondary": "#ffffff",
                    "bg_tertiary": "#f5f5f5",
                    "bg_card": "#ffffff",
                    
                    # Text
                    "text_primary": "#212121",
                    "text_secondary": "#424242",
                    "text_muted": "#757575",
                    
                    # Borders
                    "border": "#e0e0e0",
                    "border_light": "#f0f0f0",
                    "border_accent": "#1976d2",
                    
                    # Status indicators  
                    "status_online": "#388e3c",
                    "status_offline": "#d32f2f",
                    "status_maintenance": "#f57c00", 
                    "status_idle": "#757575",
                }
            }
        }
        
        self.current_theme = "modern_dark"
        self._load_custom_themes()
    
    def _load_custom_themes(self):
        """Load custom themes from configuration file"""
        try:
            theme_file = "data/custom_themes.json"
            if os.path.exists(theme_file):
                with open(theme_file, 'r') as f:
                    custom_themes = json.load(f)
                    self.themes.update(custom_themes)
        except Exception:
            pass  # Ignore errors loading custom themes
    
    def apply_theme(self, theme_name: Optional[str] = None):
        """Apply a theme system-wide"""
        if theme_name is None:
            theme_name = self.current_theme
            
        if theme_name not in self.themes:
            theme_name = "modern_dark"
            
        theme = self.themes[theme_name]
        self.current_theme = theme_name
        
        # Apply CustomTkinter settings
        ctk.set_appearance_mode(theme["appearance_mode"])
        ctk.set_default_color_theme(theme["color_theme"])
        
        return theme
    
    def get_color(self, color_key: str) -> str:
        """Get a color from current theme"""
        theme = self.themes[self.current_theme]
        return theme["colors"].get(color_key, "#ffffff")
    
    def get_theme_config(self) -> Dict[str, Any]:
        """Get current theme configuration"""
        return self.themes[self.current_theme]
    
    def create_gradient_colors(self, base_color: str, steps: int = 5) -> list:
        """Create gradient colors for advanced styling"""
        # Simplified gradient generation
        import colorsys
        
        # Convert hex to RGB
        base_rgb = tuple(int(base_color[i:i+2], 16) for i in (1, 3, 5))
        base_hsv = colorsys.rgb_to_hsv(*(x/255.0 for x in base_rgb))
        
        colors = []
        for i in range(steps):
            # Vary lightness
            h, s, v = base_hsv
            v = max(0.2, min(1.0, v + (i - steps//2) * 0.1))
            rgb = colorsys.hsv_to_rgb(h, s, v)
            hex_color = "#{:02x}{:02x}{:02x}".format(
                int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255)
            )
            colors.append(hex_color)
        
        return colors

# Global theme manager instance
theme_manager = ModernThemeManager()

def get_theme_manager() -> ModernThemeManager:
    """Get the global theme manager instance"""
    return theme_manager

def apply_modern_styling(widget, style_type: str = "default", **kwargs):
    """Apply modern styling to any widget"""
    theme = theme_manager.get_theme_config()
    colors = theme["colors"]
    
    style_configs = {
        "card": {
            "fg_color": colors["bg_card"],
            "border_color": colors["border"],
            "border_width": 1,
            "corner_radius": 8
        },
        "primary_button": {
            "fg_color": colors["primary"],
            "hover_color": colors["primary_dark"],
            "border_color": colors["primary"],
            "text_color": colors["text_primary"],
            "corner_radius": 6
        },
        "accent_button": {
            "fg_color": colors["accent"],
            "hover_color": colors["accent_dark"], 
            "border_color": colors["accent"],
            "text_color": colors["text_primary"],
            "corner_radius": 6
        },
        "success_button": {
            "fg_color": colors["success"],
            "hover_color": "#388e3c",
            "text_color": colors["text_primary"],
            "corner_radius": 6
        },
        "warning_button": {
            "fg_color": colors["warning"],
            "hover_color": "#f57c00",
            "text_color": colors["text_primary"], 
            "corner_radius": 6
        },
        "error_button": {
            "fg_color": colors["error"],
            "hover_color": "#d32f2f",
            "text_color": colors["text_primary"],
            "corner_radius": 6
        },
        "input_field": {
            "fg_color": colors["bg_secondary"],
            "border_color": colors["border"],
            "text_color": colors["text_primary"],
            "corner_radius": 4
        }
    }
    
    # Apply base style
    if style_type in style_configs:
        config = style_configs[style_type].copy()
        config.update(kwargs)  # Override with custom kwargs
        
        # Apply configuration to widget
        try:
            widget.configure(**config)
        except Exception:
            pass  # Ignore configuration errors for unsupported options

class ModernFrame(ctk.CTkFrame):
    """Modern styled frame with enhanced appearance"""
    
    def __init__(self, parent, style="card", **kwargs):
        super().__init__(parent, **kwargs)
        apply_modern_styling(self, style)

class ModernButton(ctk.CTkButton):
    """Modern styled button with enhanced appearance"""
    
    def __init__(self, parent, style="primary_button", **kwargs):
        super().__init__(parent, **kwargs)
        apply_modern_styling(self, style)

class ModernLabel(ctk.CTkLabel):
    """Modern styled label with enhanced typography"""
    
    def __init__(self, parent, text_style="primary", **kwargs):
        super().__init__(parent, **kwargs)
        
        colors = theme_manager.get_theme_config()["colors"]
        text_colors = {
            "primary": colors["text_primary"],
            "secondary": colors["text_secondary"], 
            "muted": colors["text_muted"],
            "success": colors["success"],
            "warning": colors["warning"],
            "error": colors["error"]
        }
        
        if text_style in text_colors:
            self.configure(text_color=text_colors[text_style])

class ModernEntry(ctk.CTkEntry):
    """Modern styled entry field"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        apply_modern_styling(self, "input_field")
