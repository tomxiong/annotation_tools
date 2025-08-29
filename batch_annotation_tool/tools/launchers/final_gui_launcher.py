#!/usr/bin/env python3
"""
Final Comprehensive GUI Launcher and Functionality Tester
Demonstrates all panoramic annotation tool features
"""

import sys
import os
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, filedialog
import subprocess
import traceback

def setup_environment():
    """Setup the Python environment"""
    project_root = Path(__file__).parent.absolute()
    src_path = project_root / 'src'
    
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    return project_root, src_path

def ensure_dependencies():
    """Ensure required dependencies are installed"""
    try:
        from PIL import Image, ImageTk
        return True
    except ImportError:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "Pillow"], 
                          check=True)
            return True
        except:
            return False

def create_demo_images():
    """Create demo images for testing"""
    try:
        from PIL import Image, ImageDraw
        
        # Create test directory
        test_dir = Path("D:/test/images")
        test_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"Creating demo images in: {test_dir}")
        
        # Create a sample panoramic image
        img = Image.new('RGB', (3088, 2064), color='#f0f8ff')
        draw = ImageDraw.Draw(img)
        
        # Add title
        draw.text((100, 50), "Demo Panoramic Image - Microbial Drug Sensitivity", 
                 fill='black', anchor="lt")
        draw.text((100, 100), "12×10 Hole Layout (120 holes total)", 
                 fill='blue', anchor="lt")
        
        # Draw hole grid
        for row in range(10):
            for col in range(12):
                hole_num = row * 12 + col + 1
                x = 750 + col * 145
                y = 392 + row * 145
                
                # Draw hole
                color = 'black'
                fill_color = None
                
                # Simulate different conditions
                if hole_num % 15 == 0:  # Positive growth
                    fill_color = '#90EE90'  # Light green
                elif hole_num % 13 == 0:  # Negative
                    fill_color = '#FFB6C1'  # Light pink
                
                if fill_color:
                    draw.ellipse([x-45, y-45, x+45, y+45], fill=fill_color, outline=color, width=2)
                else:
                    draw.ellipse([x-45, y-45, x+45, y+45], outline=color, width=2)
                
                # Add hole number
                text_color = 'white' if fill_color else 'black'
                draw.text((x, y), str(hole_num), fill=text_color, anchor="mm")
        
        # Save demo image
        demo_path = test_dir / "demo_panoramic_001.jpg"
        img.save(demo_path, 'JPEG', quality=90)
        
        print(f"✓ Created demo image: {demo_path}")
        return str(test_dir)
        
    except Exception as e:
        print(f"Could not create demo images: {e}")
        return None

def launch_gui_safely():
    """Launch the GUI with error handling"""
    try:
        from ui.panoramic_annotation_gui import PanoramicAnnotationGUI
        
        # Create main window
        root = tk.Tk()
        root.title("全景图像标注工具 - 微生物药敏检测 (Demo)")
        
        # Configure window
        root.geometry("2000x1200+50+50")
        root.minsize(1400, 900)
        
        # Create application
        app = PanoramicAnnotationGUI(root)
        
        # Show startup message
        messagebox.showinfo(
            "Welcome to Panoramic Annotation Tool",
            "Welcome to the Panoramic Annotation Tool!\n\n"
            "Features to test:\n"
            "1. Set panoramic directory to: D:\\test\\images\n"
            "2. Click 'Load Data' to load images\n"
            "3. Navigate holes using arrow keys or hole numbers\n"
            "4. Test annotation features (growth levels, microbe types)\n"
            "5. Save and load annotations\n"
            "6. Navigate between panoramic images\n\n"
            "The tool is ready for microbial drug sensitivity annotation!"
        )
        
        # Start the GUI
        root.mainloop()
        
        return True
        
    except Exception as e:
        error_msg = f"Failed to launch GUI: {str(e)}"
        print(error_msg)
        traceback.print_exc()
        
        try:
            messagebox.showerror("Launch Error", error_msg)
        except:
            pass
        
        return False

def show_feature_demo():
    """Show a feature demonstration window"""
    demo_window = tk.Tk()
    demo_window.title("Panoramic Annotation Tool - Feature Demo")
    demo_window.geometry("800x600")
    
    # Create notebook for different demo sections
    from tkinter import ttk
    notebook = ttk.Notebook(demo_window)
    notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Overview tab
    overview_frame = ttk.Frame(notebook)
    notebook.add(overview_frame, text="Overview")
    
    overview_text = tk.Text(overview_frame, wrap=tk.WORD, padx=10, pady=10)
    overview_text.pack(fill=tk.BOTH, expand=True)
    
    overview_content = """
全景图像标注工具 - 微生物药敏检测

This tool is designed for annotating panoramic images in microbial drug sensitivity detection.

Key Features:
• 12×10 hole layout management (120 holes total)
• Panoramic image display with navigation
• Enhanced annotation with detailed microbial characteristics
• Batch import/export functionality
• Annotation review and multi-session workflow support
• Data persistence and reload capabilities

Annotation Workflow:
1. Load panoramic images and their slice images
2. Import preliminary positive/negative results
3. Navigate through holes and enhance annotations
4. Save comprehensive annotation data for ML training
5. Review and reload saved annotations for iterative refinement

Technical Specifications:
• Supports panoramic images (recommended: 3088×2064)
• Automatic slice image organization
• JSON-based annotation storage
• Real-time navigation and positioning
• Configurable hole parameters
"""
    
    overview_text.insert("1.0", overview_content)
    overview_text.config(state="disabled")
    
    # Features tab
    features_frame = ttk.Frame(notebook)
    notebook.add(features_frame, text="Features")
    
    features_text = tk.Text(features_frame, wrap=tk.WORD, padx=10, pady=10)
    features_text.pack(fill=tk.BOTH, expand=True)
    
    features_content = """
ANNOTATION FEATURES:

1. Hole Management:
   • 12×10 grid layout (120 holes)
   • Configurable positioning parameters
   • Real-time coordinate calculation
   • Navigation using arrow keys or hole numbers

2. Image Handling:
   • Panoramic image display and scaling
   • Slice image organization and loading
   • Multi-format support (JPEG, PNG, TIFF)
   • Memory-efficient image processing

3. Annotation Categories:
   • Growth Level: negative, weak_positive, positive, strong_positive
   • Microbe Type: bacteria, fungi, mixed
   • Growth Pattern: uniform, clustered, scattered, edge_growth
   • Edge Clarity: clear, blurred, irregular
   • Interference Factors: pores, artifacts, edge_blur, contamination

4. Navigation System:
   • Panoramic navigation (previous/next)
   • Direction navigation (arrow keys)
   • Sequence navigation (first/previous/next/last)
   • Hole number input for direct access

5. Data Management:
   • JSON-based annotation storage
   • Batch import from CSV/Excel
   • Export for ML training
   • Configuration save/load
   • Multi-session annotation support
"""
    
    features_text.insert("1.0", features_content)
    features_text.config(state="disabled")
    
    # Usage tab
    usage_frame = ttk.Frame(notebook)
    notebook.add(usage_frame, text="Usage")
    
    usage_text = tk.Text(usage_frame, wrap=tk.WORD, padx=10, pady=10)
    usage_text.pack(fill=tk.BOTH, expand=True)
    
    usage_content = """
HOW TO USE THE TOOL:

1. SETUP:
   • Ensure panoramic images are in a directory
   • Organize slice images in subdirectories (optional)
   • Prepare preliminary results (CSV format, optional)

2. LAUNCHING:
   • Run: python start_gui.py
   • Or use: start_gui.bat (Windows)
   • Or use: ./start_gui.sh (Linux/Mac)

3. CONFIGURATION:
   • Set panoramic directory path
   • Enable/disable subdirectory mode
   • Configure hole positioning if needed

4. DATA LOADING:
   • Click "Load Data" to scan images
   • Verify panoramic and slice image detection
   • Check navigation functionality

5. ANNOTATION WORKFLOW:
   • Select panoramic image from dropdown
   • Navigate to holes using arrow keys or input
   • Enhance annotations with detailed characteristics
   • Save progress regularly
   • Export final annotations

6. ADVANCED FEATURES:
   • Batch import existing annotations
   • Review and modify saved annotations
   • Configure hole positioning parameters
   • Export training datasets

7. KEYBOARD SHORTCUTS:
   • Arrow keys: Navigate holes
   • Home/End: First/Last hole
   • Page Up/Down: Previous/Next panoramic
   • Ctrl+S: Save annotations
   • Ctrl+O: Load annotations

TEST DATA:
The tool can create demo images for testing at D:\\test\\images
"""
    
    usage_text.insert("1.0", usage_content)
    usage_text.config(state="disabled")
    
    # Launch button
    launch_frame = ttk.Frame(demo_window)
    launch_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
    
    ttk.Button(launch_frame, text="Launch GUI", 
              command=lambda: [demo_window.destroy(), launch_gui_safely()]).pack(side=tk.RIGHT, padx=(5, 0))
    ttk.Button(launch_frame, text="Create Demo Images", 
              command=lambda: create_demo_images()).pack(side=tk.RIGHT, padx=(5, 0))
    ttk.Button(launch_frame, text="Close Demo", 
              command=demo_window.destroy).pack(side=tk.RIGHT)
    
    demo_window.mainloop()

def main():
    """Main function"""
    print("Panoramic Annotation Tool - Final Comprehensive Launcher")
    print("=" * 60)
    
    # Setup environment
    project_root, src_path = setup_environment()
    print(f"Project root: {project_root}")
    
    # Check dependencies
    if not ensure_dependencies():
        print("Warning: Could not install Pillow. Some features may not work.")
    
    # Create demo images
    demo_dir = create_demo_images()
    if demo_dir:
        print(f"Demo images created at: {demo_dir}")
    
    # Show feature demo or launch GUI directly
    try:
        # Try to import GUI to check if it's working
        from ui.panoramic_annotation_gui import PanoramicAnnotationGUI
        
        # Ask user preference
        root = tk.Tk()
        root.withdraw()
        
        choice = messagebox.askyesno(
            "Launch Option",
            "Panoramic Annotation Tool is ready!\n\n"
            "YES: Show feature demo first\n"
            "NO: Launch GUI directly\n\n"
            "The tool supports microbial drug sensitivity annotation\n"
            "with 12×10 hole layout management."
        )
        
        root.destroy()
        
        if choice:
            show_feature_demo()
        else:
            launch_gui_safely()
    
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        
        # Show error dialog
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "Launch Error",
                f"Failed to launch the tool:\n{str(e)}\n\n"
                "Please check the console for details."
            )
            root.destroy()
        except:
            pass

if __name__ == "__main__":
    main()