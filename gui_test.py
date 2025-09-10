#!/usr/bin/env python3
"""
Simple CustomTkinter test to see if GUI works at all
"""

try:
    print("Testing basic CustomTkinter...")
    import customtkinter as ctk
    print("✓ CustomTkinter imported successfully")
    
    print("Creating simple window...")
    root = ctk.CTk()
    root.title("Test")
    root.geometry("300x200")
    print("✓ Window created")
    
    label = ctk.CTkLabel(root, text="Hello World")
    label.pack(pady=20)
    print("✓ Label added")
    
    print("Testing window display...")
    # Don't start mainloop, just test creation
    root.update()
    print("✓ Window update successful")
    
    root.destroy()
    print("✓ GUI test completed successfully")
    
except Exception as e:
    print(f"✗ GUI test failed: {e}")
    import traceback
    traceback.print_exc()
