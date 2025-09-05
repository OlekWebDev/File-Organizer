#!/usr/bin/env python3
"""
Folder Organizer v1.0
A powerful file organization tool with CustomTkinter GUI
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict, field
from enum import Enum

# Set default appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Data Classes
@dataclass
class FolderRule:
    """Represents a folder organization rule"""
    name: str
    enabled: bool = True
    hierarchy_level: int = 1
    folder_name: str = ""
    file_extensions: List[str] = field(default_factory=list)
    is_time_based: bool = False
    time_pattern: str = "MMM"  # MMM, YYYY-MM, Weekly, Daily, Yearly
    date_source: str = "modified"  # modified, created, accessed
    icon: str = "📁"

@dataclass
class FilterAction:
    """Represents a filter with its action"""
    name: str
    enabled: bool = True
    file_types: List[str] = field(default_factory=list)
    name_contains: str = ""
    date_range_start: Optional[str] = None
    date_range_end: Optional[str] = None
    older_than_days: Optional[int] = None
    action_type: str = "move"  # move, move_external, delete, exclude, rename
    destination: str = ""
    rename_pattern: str = ""
    priority: int = 0

@dataclass
class AppSettings:
    """Application settings"""
    create_backup_log: bool = True
    show_confirmation: bool = True
    delete_duplicates: bool = False
    preserve_timestamps: bool = False
    exclude_organized_folders: bool = True
    exclude_before_date: Optional[str] = None
    exclude_folders: List[str] = field(default_factory=lambda: ["node_modules", ".git", ".vscode", "__pycache__"])
    exclude_files: List[str] = field(default_factory=lambda: ["desktop.ini", "Thumbs.db", ".DS_Store"])
    batch_size: int = 100
    verbose_logging: bool = True
    log_directory: str = str(Path.home() / "Documents" / "FolderOrganizerLogs")

class FolderOrganizerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Folder Organizer v1.0")
        self.geometry("1000x750")
        
        # Initialize data
        self.target_folder = tk.StringVar(value=str(Path.home() / "Downloads"))
        self.folder_rules: List[FolderRule] = []
        self.filter_actions: List[FilterAction] = []
        self.settings = AppSettings()
        self.current_config_file = None
        
        # Initialize default rules
        self.init_default_rules()
        
        # Create GUI
        self.create_menu_bar()
        self.create_main_interface()
        self.create_status_bar()
        
        # Bind shortcuts
        self.bind('<Control-s>', lambda e: self.save_configuration())
        self.bind('<Control-o>', lambda e: self.load_configuration())
        self.bind('<Control-q>', lambda e: self.quit())
    
    def init_default_rules(self):
        """Initialize default folder rules"""
        self.folder_rules = [
            FolderRule(
                name="Time-Based Organization",
                hierarchy_level=1,
                is_time_based=True,
                time_pattern="MMM",
                date_source="modified",
                icon="📅"
            ),
            FolderRule(
                name="Images",
                hierarchy_level=2,
                folder_name="Images",
                file_extensions=[".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".ico", ".tiff", ".raw"],
                icon="📷"
            ),
            FolderRule(
                name="Documents",
                hierarchy_level=2,
                folder_name="Documents",
                file_extensions=[".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".csv", ".rtf", ".odt"],
                icon="📄"
            ),
            FolderRule(
                name="Code",
                hierarchy_level=2,
                folder_name="Code",
                file_extensions=[".js", ".py", ".html", ".css", ".java", ".cpp", ".c", ".h", ".php", ".rb", ".go", ".rs", ".swift", ".kt", ".ts", ".jsx", ".vue", ".json", ".xml", ".yaml", ".sql"],
                icon="💻"
            ),
            FolderRule(
                name="Videos",
                hierarchy_level=2,
                folder_name="Videos",
                file_extensions=[".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v", ".mpg", ".mpeg", ".3gp", ".ogv"],
                icon="🎬"
            ),
            FolderRule(
                name="Executables",
                hierarchy_level=1,
                folder_name="Exe",
                file_extensions=[".exe", ".msi", ".app", ".deb", ".dmg", ".pkg", ".bat", ".sh", ".appimage"],
                icon="⚙️"
            )
        ]
    
    def create_menu_bar(self):
        """Create the menu bar"""
        menu_frame = ctk.CTkFrame(self, height=35)
        menu_frame.pack(fill="x", padx=0, pady=0)
        
        # File menu
        file_btn = ctk.CTkButton(menu_frame, text="File", width=60, 
                                 command=self.show_file_menu)
        file_btn.pack(side="left", padx=2, pady=2)
        
        # Edit menu
        edit_btn = ctk.CTkButton(menu_frame, text="Edit", width=60,
                                 command=self.show_edit_menu)
        edit_btn.pack(side="left", padx=2, pady=2)
        
        # View menu
        view_btn = ctk.CTkButton(menu_frame, text="View", width=60,
                                 command=self.show_view_menu)
        view_btn.pack(side="left", padx=2, pady=2)
        
        # Tools menu
        tools_btn = ctk.CTkButton(menu_frame, text="Tools", width=60,
                                  command=self.show_tools_menu)
        tools_btn.pack(side="left", padx=2, pady=2)
        
        # About menu
        about_btn = ctk.CTkButton(menu_frame, text="About", width=60,
                                  command=self.show_about)
        about_btn.pack(side="left", padx=2, pady=2)
    
    def create_main_interface(self):
        """Create the main interface"""
        # Target folder selection
        folder_frame = ctk.CTkFrame(self)
        folder_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(folder_frame, text="Target Folder:").pack(side="left", padx=5)
        
        folder_entry = ctk.CTkEntry(folder_frame, textvariable=self.target_folder, width=500)
        folder_entry.pack(side="left", padx=5, fill="x", expand=True)
        
        browse_btn = ctk.CTkButton(folder_frame, text="Browse...", width=100,
                                   command=self.browse_folder)
        browse_btn.pack(side="left", padx=5)
        
        # Notebook for tabs
        self.notebook = ctk.CTkTabview(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Create tabs
        self.create_folder_rules_tab()
        self.create_filters_actions_tab()
        self.create_preview_tab()
        self.create_settings_tab()
        
        # Bottom controls
        self.create_bottom_controls()
    
    def create_folder_rules_tab(self):
        """Create the Folder Rules tab"""
        tab = self.notebook.add("Folder Rules")
        
        # Buttons frame
        btn_frame = ctk.CTkFrame(tab)
        btn_frame.pack(fill="x", padx=5, pady=5)
        
        add_btn = ctk.CTkButton(btn_frame, text="+ Add Folder Rule",
                               command=self.add_folder_rule)
        add_btn.pack(side="left", padx=5)
        
        # Scrollable frame for rules
        self.rules_scroll = ctk.CTkScrollableFrame(tab, height=400)
        self.rules_scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Display default rules
        self.refresh_folder_rules_display()
    
    def create_filters_actions_tab(self):
        """Create the Filters/Actions tab"""
        tab = self.notebook.add("Filters/Actions")
        
        # Buttons frame
        btn_frame = ctk.CTkFrame(tab)
        btn_frame.pack(fill="x", padx=5, pady=5)
        
        add_btn = ctk.CTkButton(btn_frame, text="+ Add Filter",
                               command=self.add_filter_action)
        add_btn.pack(side="left", padx=5)
        
        # Scrollable frame for filters
        self.filters_scroll = ctk.CTkScrollableFrame(tab, height=400)
        self.filters_scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Add example filters
        self.add_example_filters()
        self.refresh_filters_display()
    
    def create_preview_tab(self):
        """Create the Preview tab"""
        tab = self.notebook.add("Preview")
        
        # Preview text widget
        self.preview_text = ctk.CTkTextbox(tab, wrap="none", font=("Courier", 12))
        self.preview_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Refresh button
        refresh_btn = ctk.CTkButton(tab, text="Refresh Preview",
                                    command=self.update_preview)
        refresh_btn.pack(pady=5)
        
        # Initial preview
        self.update_preview()
    
    def create_settings_tab(self):
        """Create the Settings tab"""
        tab = self.notebook.add("Settings")
        
        # Scrollable frame for settings
        scroll = ctk.CTkScrollableFrame(tab)
        scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        # General Settings
        general_frame = ctk.CTkFrame(scroll)
        general_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(general_frame, text="General Settings", 
                    font=("Arial", 14, "bold")).pack(anchor="w", padx=5, pady=5)
        
        self.backup_var = tk.BooleanVar(value=self.settings.create_backup_log)
        ctk.CTkCheckBox(general_frame, text="Create backup log file",
                       variable=self.backup_var).pack(anchor="w", padx=20, pady=2)
        
        self.confirm_var = tk.BooleanVar(value=self.settings.show_confirmation)
        ctk.CTkCheckBox(general_frame, text="Show confirmation before organizing",
                       variable=self.confirm_var).pack(anchor="w", padx=20, pady=2)
        
        self.duplicates_var = tk.BooleanVar(value=self.settings.delete_duplicates)
        ctk.CTkCheckBox(general_frame, text="Delete duplicate files (keep newest)",
                       variable=self.duplicates_var).pack(anchor="w", padx=20, pady=2)
        
        # Exclusions
        exclude_frame = ctk.CTkFrame(scroll)
        exclude_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(exclude_frame, text="Exclusions",
                    font=("Arial", 14, "bold")).pack(anchor="w", padx=5, pady=5)
        
        self.exclude_organized_var = tk.BooleanVar(value=self.settings.exclude_organized_folders)
        ctk.CTkCheckBox(exclude_frame, text="Exclude already organized folders",
                       variable=self.exclude_organized_var).pack(anchor="w", padx=20, pady=2)
        
        date_frame = ctk.CTkFrame(exclude_frame)
        date_frame.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(date_frame, text="Exclude before:").pack(side="left", padx=5)
        self.exclude_date_entry = ctk.CTkEntry(date_frame, width=150, 
                                               placeholder_text="YYYY-MM-DD")
        self.exclude_date_entry.pack(side="left", padx=5)
        
        ctk.CTkLabel(exclude_frame, text="Exclude folders:").pack(anchor="w", padx=20, pady=(10, 2))
        self.exclude_folders_text = ctk.CTkTextbox(exclude_frame, height=80, width=400)
        self.exclude_folders_text.pack(padx=20, pady=2)
        self.exclude_folders_text.insert("1.0", "\n".join(self.settings.exclude_folders))
        
        ctk.CTkLabel(exclude_frame, text="Exclude files:").pack(anchor="w", padx=20, pady=(10, 2))
        self.exclude_files_text = ctk.CTkTextbox(exclude_frame, height=80, width=400)
        self.exclude_files_text.pack(padx=20, pady=2)
        self.exclude_files_text.insert("1.0", "\n".join(self.settings.exclude_files))
    
    def create_bottom_controls(self):
        """Create bottom control buttons"""
        bottom_frame = ctk.CTkFrame(self)
        bottom_frame.pack(fill="x", padx=10, pady=5)
        
        # Left side - checkboxes
        left_frame = ctk.CTkFrame(bottom_frame)
        left_frame.pack(side="left", padx=5)
        
        self.preview_var = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(left_frame, text="Preview Changes",
                       variable=self.preview_var).pack(side="left", padx=5)
        
        self.backup_log_var = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(left_frame, text="Create Backup Log",
                       variable=self.backup_log_var).pack(side="left", padx=5)
        
        # Right side - action buttons
        right_frame = ctk.CTkFrame(bottom_frame)
        right_frame.pack(side="right", padx=5)
        
        dry_run_btn = ctk.CTkButton(right_frame, text="Dry Run", width=100,
                                    command=self.dry_run)
        dry_run_btn.pack(side="left", padx=5)
        
        organize_btn = ctk.CTkButton(right_frame, text="Organize Files", width=120,
                                     fg_color="green", hover_color="darkgreen",
                                     command=self.organize_files)
        organize_btn.pack(side="left", padx=5)
    
    def create_status_bar(self):
        """Create status bar"""
        self.status_bar = ctk.CTkLabel(self, text="Ready", anchor="w")
        self.status_bar.pack(fill="x", padx=10, pady=(0, 5))
    
    def refresh_folder_rules_display(self):
        """Refresh the folder rules display"""
        # Clear existing widgets
        for widget in self.rules_scroll.winfo_children():
            widget.destroy()
        
        # Display each rule
        for i, rule in enumerate(self.folder_rules):
            self.create_rule_widget(self.rules_scroll, rule, i)
    
    def create_rule_widget(self, parent, rule: FolderRule, index: int):
        """Create a widget for a folder rule"""
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", padx=5, pady=5)
        
        # Header
        header_frame = ctk.CTkFrame(frame)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        # Checkbox and title
        enabled_var = tk.BooleanVar(value=rule.enabled)
        enabled_var.trace("w", lambda *args: self.toggle_rule(index, enabled_var.get()))
        
        ctk.CTkCheckBox(header_frame, text=f"{rule.icon} {rule.name}",
                       variable=enabled_var, font=("Arial", 12, "bold")).pack(side="left")
        
        # Control buttons
        btn_frame = ctk.CTkFrame(header_frame)
        btn_frame.pack(side="right")
        
        edit_btn = ctk.CTkButton(btn_frame, text="Edit", width=50,
                                command=lambda: self.edit_rule(index))
        edit_btn.pack(side="left", padx=2)
        
        delete_btn = ctk.CTkButton(btn_frame, text="Delete", width=50,
                                   fg_color="red", hover_color="darkred",
                                   command=lambda: self.delete_rule(index))
        delete_btn.pack(side="left", padx=2)
        
        # Details
        details_frame = ctk.CTkFrame(frame)
        details_frame.pack(fill="x", padx=20, pady=5)
        
        if rule.is_time_based:
            ctk.CTkLabel(details_frame, text=f"Pattern: {rule.time_pattern}").pack(anchor="w")
            ctk.CTkLabel(details_frame, text=f"Date Source: {rule.date_source}").pack(anchor="w")
        else:
            ctk.CTkLabel(details_frame, text=f"Folder: {rule.folder_name}").pack(anchor="w")
            if rule.file_extensions:
                ext_text = ", ".join(rule.file_extensions[:10])
                if len(rule.file_extensions) > 10:
                    ext_text += "..."
                ctk.CTkLabel(details_frame, text=f"Extensions: {ext_text}").pack(anchor="w")
        
        ctk.CTkLabel(details_frame, text=f"Hierarchy Level: {rule.hierarchy_level}").pack(anchor="w")
    
    def refresh_filters_display(self):
        """Refresh the filters display"""
        # Clear existing widgets
        for widget in self.filters_scroll.winfo_children():
            widget.destroy()
        
        # Display each filter
        for i, filter_action in enumerate(self.filter_actions):
            self.create_filter_widget(self.filters_scroll, filter_action, i)
    
    def create_filter_widget(self, parent, filter_action: FilterAction, index: int):
        """Create a widget for a filter/action"""
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", padx=5, pady=5)
        
        # Header
        header_frame = ctk.CTkFrame(frame)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        # Checkbox and title
        enabled_var = tk.BooleanVar(value=filter_action.enabled)
        enabled_var.trace("w", lambda *args: self.toggle_filter(index, enabled_var.get()))
        
        ctk.CTkCheckBox(header_frame, text=filter_action.name,
                       variable=enabled_var, font=("Arial", 12, "bold")).pack(side="left")
        
        # Control buttons
        btn_frame = ctk.CTkFrame(header_frame)
        btn_frame.pack(side="right")
        
        edit_btn = ctk.CTkButton(btn_frame, text="Edit", width=50,
                                command=lambda: self.edit_filter(index))
        edit_btn.pack(side="left", padx=2)
        
        delete_btn = ctk.CTkButton(btn_frame, text="Delete", width=50,
                                   fg_color="red", hover_color="darkred",
                                   command=lambda: self.delete_filter(index))
        delete_btn.pack(side="left", padx=2)
        
        # Conditions
        cond_frame = ctk.CTkFrame(frame)
        cond_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(cond_frame, text="Conditions:", font=("Arial", 10, "bold")).pack(anchor="w")
        
        if filter_action.file_types:
            ctk.CTkLabel(cond_frame, text=f"  File types: {', '.join(filter_action.file_types)}").pack(anchor="w")
        if filter_action.name_contains:
            ctk.CTkLabel(cond_frame, text=f"  Name contains: {filter_action.name_contains}").pack(anchor="w")
        if filter_action.older_than_days:
            ctk.CTkLabel(cond_frame, text=f"  Older than: {filter_action.older_than_days} days").pack(anchor="w")
        
        # Action
        action_frame = ctk.CTkFrame(frame)
        action_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(action_frame, text=f"Action: {filter_action.action_type}",
                    font=("Arial", 10, "bold")).pack(anchor="w")
        
        if filter_action.destination:
            ctk.CTkLabel(action_frame, text=f"  Destination: {filter_action.destination}").pack(anchor="w")
    
    def add_example_filters(self):
        """Add example filter actions"""
        self.filter_actions = [
            FilterAction(
                name="Invoice Handler",
                file_types=[".pdf", ".xlsx"],
                name_contains="invoice",
                action_type="move_external",
                destination=str(Path.home() / "Documents" / "Invoices")
            ),
            FilterAction(
                name="Delete Old Temp Files",
                file_types=[".tmp", ".temp", ".cache"],
                older_than_days=30,
                action_type="delete"
            )
        ]
    
    def update_preview(self):
        """Update the preview tree"""
        self.preview_text.delete("1.0", "end")
        
        preview = self.generate_preview_tree()
        self.preview_text.insert("1.0", preview)
    
    def generate_preview_tree(self):
        """Generate a preview of the folder structure"""
        tree = f"📁 {os.path.basename(self.target_folder.get())}/\n\n"
        
        # Sort rules by hierarchy level
        sorted_rules = sorted(self.folder_rules, key=lambda r: (r.hierarchy_level, r.name))
        
        # Generate sample structure
        level1_rules = [r for r in sorted_rules if r.hierarchy_level == 1 and r.enabled]
        level2_rules = [r for r in sorted_rules if r.hierarchy_level == 2 and r.enabled]
        
        for i, l1_rule in enumerate(level1_rules):
            is_last_l1 = (i == len(level1_rules) - 1)
            prefix = "└── " if is_last_l1 else "├── "
            
            if l1_rule.is_time_based:
                # Show a few time-based folders
                months = ["Sep", "Aug", "Jul"] if l1_rule.time_pattern == "MMM" else ["2024-09", "2024-08", "2024-07"]
                for j, month in enumerate(months):
                    is_last_month = (j == len(months) - 1) and is_last_l1
                    month_prefix = "└── " if is_last_month else "├── "
                    tree += f"    {month_prefix}📅 {month}/\n"
                    
                    # Add level 2 folders under each time folder
                    for k, l2_rule in enumerate(level2_rules):
                        is_last_l2 = (k == len(level2_rules) - 1)
                        l2_prefix = "└── " if is_last_l2 else "├── "
                        indent = "    " if is_last_month else "│   "
                        tree += f"    {indent}    {l2_prefix}{l2_rule.icon} {l2_rule.folder_name}/\n"
                        
                        # Add sample files
                        if k == 0:  # Just show files in first folder
                            tree += f"    {indent}    {'    ' if is_last_l2 else '│   '}    ├── sample_file1.ext\n"
                            tree += f"    {indent}    {'    ' if is_last_l2 else '│   '}    └── sample_file2.ext\n"
                    
                    if j < len(months) - 1:
                        tree += "    │\n"
            else:
                # Regular folder
                tree += f"    {prefix}{l1_rule.icon} {l1_rule.folder_name}/\n"
                tree += f"    {'    ' if is_last_l1 else '│   '}├── sample_file1.ext\n"
                tree += f"    {'    ' if is_last_l1 else '│   '}└── sample_file2.ext\n"
            
            if i < len(level1_rules) - 1:
                tree += "    │\n"
        
        # Add statistics
        tree += "\n" + "="*50 + "\n"
        tree += "Statistics:\n"
        tree += f"• Target folder: {self.target_folder.get()}\n"
        tree += f"• Active folder rules: {sum(1 for r in self.folder_rules if r.enabled)}\n"
        tree += f"• Active filters: {sum(1 for f in self.filter_actions if f.enabled)}\n"
        tree += f"• Estimated folders to create: {self.estimate_folders()}\n"
        
        return tree
    
    def estimate_folders(self):
        """Estimate number of folders to create"""
        count = 0
        for rule in self.folder_rules:
            if rule.enabled:
                if rule.is_time_based:
                    count += 3  # Assume 3 months for now
                    count += 3 * sum(1 for r in self.folder_rules if r.hierarchy_level == 2 and r.enabled)
                else:
                    count += 1
        return count
    
    # Menu actions
    def show_file_menu(self):
        """Show file menu"""
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="New Configuration", command=self.new_configuration)
        menu.add_command(label="Load Configuration", command=self.load_configuration)
        menu.add_command(label="Save Configuration", command=self.save_configuration)
        menu.add_command(label="Save As...", command=self.save_configuration_as)
        menu.add_separator()
        menu.add_command(label="Exit", command=self.quit)
        
        # Show menu at button position
        menu.post(self.winfo_pointerx(), self.winfo_pointery())
    
    def show_edit_menu(self):
        """Show edit menu"""
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Clear All Rules", command=self.clear_all_rules)
        menu.add_command(label="Reset to Defaults", command=self.reset_to_defaults)
        
        menu.post(self.winfo_pointerx(), self.winfo_pointery())
    
    def show_view_menu(self):
        """Show view menu with theme options"""
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Dark Mode", command=lambda: ctk.set_appearance_mode("dark"))
        menu.add_command(label="Light Mode", command=lambda: ctk.set_appearance_mode("light"))
        menu.add_command(label="System Mode", command=lambda: ctk.set_appearance_mode("system"))
        
        menu.post(self.winfo_pointerx(), self.winfo_pointery())
    
    def show_tools_menu(self):
        """Show tools menu"""
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Analyze Folder", command=self.analyze_folder)
        menu.add_command(label="Find Duplicates", command=self.find_duplicates)
        menu.add_command(label="Clean Empty Folders", command=self.clean_empty_folders)
        
        menu.post(self.winfo_pointerx(), self.winfo_pointery())
    
    def show_about(self):
        """Show about dialog"""
        about_window = ctk.CTkToplevel(self)
        about_window.title("About")
        about_window.geometry("400x300")
        
        ctk.CTkLabel(about_window, text="Folder Organizer v1.0",
                    font=("Arial", 18, "bold")).pack(pady=20)
        
        about_text = """A powerful file organization tool that helps you
automatically organize your folders with custom rules.

Features:
• Time-based organization
• File type categorization
• Custom filters and actions
• Preview before organizing
• Backup and restore

Created with Python and CustomTkinter"""
        
        ctk.CTkLabel(about_window, text=about_text, justify="left").pack(pady=20)
        
        ctk.CTkButton(about_window, text="Close", 
                     command=about_window.destroy).pack(pady=10)
    
    # File operations
    def browse_folder(self):
        """Browse for target folder"""
        folder = filedialog.askdirectory(initialdir=self.target_folder.get())
        if folder:
            self.target_folder.set(folder)
            self.update_status(f"Selected folder: {folder}")
            self.update_preview()
    
    def new_configuration(self):
        """Create new configuration"""
        if messagebox.askyesno("New Configuration", 
                               "This will reset all rules. Continue?"):
            self.init_default_rules()
            self.filter_actions = []
            self.refresh_folder_rules_display()
            self.refresh_filters_display()
            self.update_preview()
            self.current_config_file = None
            self.update_status("New configuration created")
    
    def save_configuration(self):
        """Save current configuration"""
        if not self.current_config_file:
            self.save_configuration_as()
        else:
            self.save_config_to_file(self.current_config_file)
    
    def save_configuration_as(self):
        """Save configuration with new filename"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            self.save_config_to_file(file_path)
            self.current_config_file = file_path
    
    def save_config_to_file(self, file_path):
        """Save configuration to file"""
        config = {
            "target_folder": self.target_folder.get(),
            "folder_rules": [asdict(rule) for rule in self.folder_rules],
            "filter_actions": [asdict(filter_action) for filter_action in self.filter_actions],
            "settings": asdict(self.settings)
        }
        
        try:
            with open(file_path, 'w') as f:
                json.dump(config, f, indent=2)
            self.update_status(f"Configuration saved to {file_path}")
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save configuration: {str(e)}")
    
    def load_configuration(self):
        """Load configuration from file"""
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            self.load_config_from_file(file_path)
    
    def load_config_from_file(self, file_path):
        """Load configuration from file"""
        try:
            with open(file_path, 'r') as f:
                config = json.load(f)
            
            self.target_folder.set(config.get("target_folder", ""))
            
            # Load folder rules
            self.folder_rules = []
            for rule_dict in config.get("folder_rules", []):
                self.folder_rules.append(FolderRule(**rule_dict))
            
            # Load filter actions
            self.filter_actions = []
            for filter_dict in config.get("filter_actions", []):
                self.filter_actions.append(FilterAction(**filter_dict))
            
            # Load settings
            if "settings" in config:
                self.settings = AppSettings(**config["settings"])
            
            self.current_config_file = file_path
            self.refresh_folder_rules_display()
            self.refresh_filters_display()
            self.update_preview()
            self.update_status(f"Configuration loaded from {file_path}")
            
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load configuration: {str(e)}")
    
    # Rule management
    def add_folder_rule(self):
        """Add new folder rule"""
        dialog = FolderRuleDialog(self, None)
        self.wait_window(dialog)
        
        if dialog.result:
            self.folder_rules.append(dialog.result)
            self.refresh_folder_rules_display()
            self.update_preview()
    
    def edit_rule(self, index):
        """Edit existing folder rule"""
        dialog = FolderRuleDialog(self, self.folder_rules[index])
        self.wait_window(dialog)
        
        if dialog.result:
            self.folder_rules[index] = dialog.result
            self.refresh_folder_rules_display()
            self.update_preview()
    
    def delete_rule(self, index):
        """Delete folder rule"""
        if messagebox.askyesno("Delete Rule", 
                               f"Delete rule '{self.folder_rules[index].name}'?"):
            del self.folder_rules[index]
            self.refresh_folder_rules_display()
            self.update_preview()
    
    def toggle_rule(self, index, enabled):
        """Toggle rule enabled state"""
        self.folder_rules[index].enabled = enabled
        self.update_preview()
    
    # Filter management
    def add_filter_action(self):
        """Add new filter action"""
        dialog = FilterActionDialog(self, None)
        self.wait_window(dialog)
        
        if dialog.result:
            self.filter_actions.append(dialog.result)
            self.refresh_filters_display()
    
    def edit_filter(self, index):
        """Edit existing filter"""
        dialog = FilterActionDialog(self, self.filter_actions[index])
        self.wait_window(dialog)
        
        if dialog.result:
            self.filter_actions[index] = dialog.result
            self.refresh_filters_display()
    
    def delete_filter(self, index):
        """Delete filter"""
        if messagebox.askyesno("Delete Filter", 
                               f"Delete filter '{self.filter_actions[index].name}'?"):
            del self.filter_actions[index]
            self.refresh_filters_display()
    
    def toggle_filter(self, index, enabled):
        """Toggle filter enabled state"""
        self.filter_actions[index].enabled = enabled
    
    # Other menu actions
    def clear_all_rules(self):
        """Clear all rules"""
        if messagebox.askyesno("Clear All", "Remove all rules and filters?"):
            self.folder_rules = []
            self.filter_actions = []
            self.refresh_folder_rules_display()
            self.refresh_filters_display()
            self.update_preview()
    
    def reset_to_defaults(self):
        """Reset to default rules"""
        if messagebox.askyesno("Reset", "Reset to default rules?"):
            self.init_default_rules()
            self.add_example_filters()
            self.refresh_folder_rules_display()
            self.refresh_filters_display()
            self.update_preview()
    
    def analyze_folder(self):
        """Analyze target folder"""
        folder = self.target_folder.get()
        if not os.path.exists(folder):
            messagebox.showerror("Error", "Target folder does not exist")
            return
        
        # Count files by extension
        ext_count = {}
        total_files = 0
        total_size = 0
        
        for root, dirs, files in os.walk(folder):
            for file in files:
                total_files += 1
                ext = os.path.splitext(file)[1].lower()
                ext_count[ext] = ext_count.get(ext, 0) + 1
                
                file_path = os.path.join(root, file)
                try:
                    total_size += os.path.getsize(file_path)
                except:
                    pass
        
        # Show results
        result_window = ctk.CTkToplevel(self)
        result_window.title("Folder Analysis")
        result_window.geometry("500x400")
        
        ctk.CTkLabel(result_window, text="Folder Analysis Results",
                    font=("Arial", 16, "bold")).pack(pady=10)
        
        info_text = f"Total files: {total_files}\n"
        info_text += f"Total size: {total_size / (1024*1024):.2f} MB\n\n"
        info_text += "Top file types:\n"
        
        sorted_exts = sorted(ext_count.items(), key=lambda x: x[1], reverse=True)[:10]
        for ext, count in sorted_exts:
            if ext:
                info_text += f"  {ext}: {count} files\n"
        
        text_widget = ctk.CTkTextbox(result_window, width=450, height=300)
        text_widget.pack(padx=10, pady=10)
        text_widget.insert("1.0", info_text)
        text_widget.configure(state="disabled")
        
        ctk.CTkButton(result_window, text="Close",
                     command=result_window.destroy).pack(pady=10)
    
    def find_duplicates(self):
        """Find duplicate files"""
        messagebox.showinfo("Find Duplicates", 
                           "Duplicate finder will be implemented in the organization engine")
    
    def clean_empty_folders(self):
        """Clean empty folders"""
        messagebox.showinfo("Clean Empty Folders", 
                           "Empty folder cleaner will be implemented in the organization engine")
    
    # Main operations
    def dry_run(self):
        """Perform dry run"""
        self.organize_files(dry_run=True)
    
    def organize_files(self, dry_run=False):
        """Main organization function"""
        folder = self.target_folder.get()
        
        if not os.path.exists(folder):
            messagebox.showerror("Error", "Target folder does not exist")
            return
        
        if self.confirm_var.get() and not dry_run:
            if not messagebox.askyesno("Confirm", 
                                       "Start organizing files?\n\nThis will move files according to your rules."):
                return
        
        # Create organizer instance
        organizer = FolderOrganizer(
            target_folder=folder,
            folder_rules=self.folder_rules,
            filter_actions=self.filter_actions,
            settings=self.settings,
            dry_run=dry_run
        )
        
        # Show progress window
        progress_window = ProgressWindow(self, organizer, dry_run)
        progress_window.start_organization()
    
    def update_status(self, message):
        """Update status bar"""
        self.status_bar.configure(text=message)


class FolderRuleDialog(ctk.CTkToplevel):
    """Dialog for adding/editing folder rules"""
    
    def __init__(self, parent, rule: Optional[FolderRule] = None):
        super().__init__(parent)
        
        self.title("Edit Folder Rule" if rule else "Add Folder Rule")
        self.geometry("500x600")
        self.result = None
        
        # Create form
        form_frame = ctk.CTkScrollableFrame(self)
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Name
        ctk.CTkLabel(form_frame, text="Rule Name:").pack(anchor="w", pady=(10, 2))
        self.name_entry = ctk.CTkEntry(form_frame, width=400)
        self.name_entry.pack(fill="x", pady=(0, 10))
        
        # Rule Type
        ctk.CTkLabel(form_frame, text="Rule Type:").pack(anchor="w", pady=(10, 2))
        self.is_time_based = tk.BooleanVar(value=rule.is_time_based if rule else False)
        
        type_frame = ctk.CTkFrame(form_frame)
        type_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkRadioButton(type_frame, text="Regular Folder", 
                          variable=self.is_time_based, value=False,
                          command=self.toggle_type).pack(side="left", padx=10)
        ctk.CTkRadioButton(type_frame, text="Time-Based", 
                          variable=self.is_time_based, value=True,
                          command=self.toggle_type).pack(side="left", padx=10)
        
        # Hierarchy Level
        ctk.CTkLabel(form_frame, text="Hierarchy Level:").pack(anchor="w", pady=(10, 2))
        self.level_slider = ctk.CTkSlider(form_frame, from_=1, to=5, number_of_steps=4)
        self.level_slider.pack(fill="x", pady=(0, 5))
        self.level_label = ctk.CTkLabel(form_frame, text="Level: 1")
        self.level_label.pack(anchor="w", pady=(0, 10))
        self.level_slider.configure(command=self.update_level_label)
        
        # Regular folder options
        self.folder_frame = ctk.CTkFrame(form_frame)
        self.folder_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(self.folder_frame, text="Folder Name:").pack(anchor="w", pady=(0, 2))
        self.folder_name_entry = ctk.CTkEntry(self.folder_frame, width=400)
        self.folder_name_entry.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(self.folder_frame, text="File Extensions (comma-separated):").pack(anchor="w", pady=(0, 2))
        self.extensions_text = ctk.CTkTextbox(self.folder_frame, height=100)
        self.extensions_text.pack(fill="x", pady=(0, 10))
        
        # Time-based options
        self.time_frame = ctk.CTkFrame(form_frame)
        
        ctk.CTkLabel(self.time_frame, text="Time Pattern:").pack(anchor="w", pady=(0, 2))
        self.pattern_menu = ctk.CTkOptionMenu(self.time_frame, 
                                              values=["MMM", "YYYY-MM", "Weekly", "Daily", "Yearly"])
        self.pattern_menu.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(self.time_frame, text="Date Source:").pack(anchor="w", pady=(0, 2))
        self.date_source_menu = ctk.CTkOptionMenu(self.time_frame,
                                                  values=["modified", "created", "accessed"])
        self.date_source_menu.pack(fill="x", pady=(0, 10))
        
        # Icon
        ctk.CTkLabel(form_frame, text="Icon (emoji):").pack(anchor="w", pady=(10, 2))
        self.icon_entry = ctk.CTkEntry(form_frame, width=100)
        self.icon_entry.pack(anchor="w", pady=(0, 10))
        
        # Buttons
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkButton(btn_frame, text="Cancel", width=100,
                     command=self.destroy).pack(side="right", padx=5)
        ctk.CTkButton(btn_frame, text="Save", width=100,
                     command=self.save).pack(side="right", padx=5)
        
        # Load existing rule
        if rule:
            self.name_entry.insert(0, rule.name)
            self.level_slider.set(rule.hierarchy_level)
            self.update_level_label(rule.hierarchy_level)
            self.icon_entry.insert(0, rule.icon)
            
            if rule.is_time_based:
                self.pattern_menu.set(rule.time_pattern)
                self.date_source_menu.set(rule.date_source)
            else:
                self.folder_name_entry.insert(0, rule.folder_name)
                self.extensions_text.insert("1.0", ", ".join(rule.file_extensions))
        else:
            self.icon_entry.insert(0, "📁")
        
        self.toggle_type()
    
    def toggle_type(self):
        """Toggle between regular and time-based"""
        if self.is_time_based.get():
            self.folder_frame.pack_forget()
            self.time_frame.pack(fill="x", pady=10, before=self.icon_entry.master)
        else:
            self.time_frame.pack_forget()
            self.folder_frame.pack(fill="x", pady=10, before=self.icon_entry.master)
    
    def update_level_label(self, value):
        """Update level label"""
        self.level_label.configure(text=f"Level: {int(value)}")
    
    def save(self):
        """Save the rule"""
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showerror("Error", "Please enter a rule name")
            return
        
        if self.is_time_based.get():
            self.result = FolderRule(
                name=name,
                hierarchy_level=int(self.level_slider.get()),
                is_time_based=True,
                time_pattern=self.pattern_menu.get(),
                date_source=self.date_source_menu.get(),
                icon=self.icon_entry.get() or "📅"
            )
        else:
            folder_name = self.folder_name_entry.get().strip()
            if not folder_name:
                messagebox.showerror("Error", "Please enter a folder name")
                return
            
            extensions_text = self.extensions_text.get("1.0", "end").strip()
            extensions = [ext.strip() for ext in extensions_text.split(",") if ext.strip()]
            
            self.result = FolderRule(
                name=name,
                hierarchy_level=int(self.level_slider.get()),
                folder_name=folder_name,
                file_extensions=extensions,
                icon=self.icon_entry.get() or "📁"
            )
        
        self.destroy()


class FilterActionDialog(ctk.CTkToplevel):
    """Dialog for adding/editing filter actions"""
    
    def __init__(self, parent, filter_action: Optional[FilterAction] = None):
        super().__init__(parent)
        
        self.title("Edit Filter" if filter_action else "Add Filter")
        self.geometry("500x650")
        self.result = None
        
        # Create form
        form_frame = ctk.CTkScrollableFrame(self)
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Name
        ctk.CTkLabel(form_frame, text="Filter Name:").pack(anchor="w", pady=(10, 2))
        self.name_entry = ctk.CTkEntry(form_frame, width=400)
        self.name_entry.pack(fill="x", pady=(0, 10))
        
        # Filter Conditions
        ctk.CTkLabel(form_frame, text="Filter Conditions:",
                    font=("Arial", 12, "bold")).pack(anchor="w", pady=(20, 10))
        
        # File types
        ctk.CTkLabel(form_frame, text="File Types (comma-separated):").pack(anchor="w", pady=(0, 2))
        self.file_types_entry = ctk.CTkEntry(form_frame, width=400)
        self.file_types_entry.pack(fill="x", pady=(0, 10))
        
        # Name contains
        ctk.CTkLabel(form_frame, text="Name Contains:").pack(anchor="w", pady=(0, 2))
        self.name_contains_entry = ctk.CTkEntry(form_frame, width=400)
        self.name_contains_entry.pack(fill="x", pady=(0, 10))
        
        # Older than days
        ctk.CTkLabel(form_frame, text="Older Than (days):").pack(anchor="w", pady=(0, 2))
        self.older_than_entry = ctk.CTkEntry(form_frame, width=100)
        self.older_than_entry.pack(anchor="w", pady=(0, 10))
        
        # Action
        ctk.CTkLabel(form_frame, text="Action:",
                    font=("Arial", 12, "bold")).pack(anchor="w", pady=(20, 10))
        
        self.action_var = tk.StringVar(value="move")
        actions = [
            ("Move to folder in structure", "move"),
            ("Move to external directory", "move_external"),
            ("Delete", "delete"),
            ("Exclude from processing", "exclude"),
            ("Rename (add prefix/suffix)", "rename")
        ]
        
        for text, value in actions:
            ctk.CTkRadioButton(form_frame, text=text, variable=self.action_var,
                              value=value, command=self.toggle_action).pack(anchor="w", padx=20, pady=2)
        
        # Destination
        self.dest_frame = ctk.CTkFrame(form_frame)
        self.dest_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(self.dest_frame, text="Destination:").pack(anchor="w", pady=(0, 2))
        dest_entry_frame = ctk.CTkFrame(self.dest_frame)
        dest_entry_frame.pack(fill="x")
        self.destination_entry = ctk.CTkEntry(dest_entry_frame, width=350)
        self.destination_entry.pack(side="left", padx=(0, 5))
        ctk.CTkButton(dest_entry_frame, text="Browse", width=70,
                     command=self.browse_destination).pack(side="left")
        
        # Rename pattern
        self.rename_frame = ctk.CTkFrame(form_frame)
        
        ctk.CTkLabel(self.rename_frame, text="Rename Pattern:").pack(anchor="w", pady=(0, 2))
        self.rename_entry = ctk.CTkEntry(self.rename_frame, width=400,
                                        placeholder_text="e.g., prefix_{original} or {original}_suffix")
        self.rename_entry.pack(fill="x")
        
        # Priority
        ctk.CTkLabel(form_frame, text="Priority (higher runs first):").pack(anchor="w", pady=(20, 2))
        self.priority_slider = ctk.CTkSlider(form_frame, from_=0, to=10, number_of_steps=10)
        self.priority_slider.pack(fill="x", pady=(0, 5))
        self.priority_label = ctk.CTkLabel(form_frame, text="Priority: 0")
        self.priority_label.pack(anchor="w", pady=(0, 10))
        self.priority_slider.configure(command=self.update_priority_label)
        
        # Buttons
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkButton(btn_frame, text="Cancel", width=100,
                     command=self.destroy).pack(side="right", padx=5)
        ctk.CTkButton(btn_frame, text="Save", width=100,
                     command=self.save).pack(side="right", padx=5)
        
        # Load existing filter
        if filter_action:
            self.name_entry.insert(0, filter_action.name)
            if filter_action.file_types:
                self.file_types_entry.insert(0, ", ".join(filter_action.file_types))
            if filter_action.name_contains:
                self.name_contains_entry.insert(0, filter_action.name_contains)
            if filter_action.older_than_days:
                self.older_than_entry.insert(0, str(filter_action.older_than_days))
            self.action_var.set(filter_action.action_type)
            if filter_action.destination:
                self.destination_entry.insert(0, filter_action.destination)
            if filter_action.rename_pattern:
                self.rename_entry.insert(0, filter_action.rename_pattern)
            self.priority_slider.set(filter_action.priority)
            self.update_priority_label(filter_action.priority)
        
        self.toggle_action()
    
    def toggle_action(self):
        """Toggle action-specific fields"""
        action = self.action_var.get()
        
        self.dest_frame.pack_forget()
        self.rename_frame.pack_forget()
        
        if action in ["move", "move_external"]:
            self.dest_frame.pack(fill="x", pady=10, after=self.action_var.trace_info()[0])
        elif action == "rename":
            self.rename_frame.pack(fill="x", pady=10, after=self.action_var.trace_info()[0])
    
    def browse_destination(self):
        """Browse for destination folder"""
        folder = filedialog.askdirectory()
        if folder:
            self.destination_entry.delete(0, "end")
            self.destination_entry.insert(0, folder)
    
    def update_priority_label(self, value):
        """Update priority label"""
        self.priority_label.configure(text=f"Priority: {int(value)}")
    
    def save(self):
        """Save the filter"""
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showerror("Error", "Please enter a filter name")
            return
        
        # Parse file types
        file_types_text = self.file_types_entry.get().strip()
        file_types = [ft.strip() for ft in file_types_text.split(",") if ft.strip()]
        
        # Parse older than days
        older_than = None
        if self.older_than_entry.get().strip():
            try:
                older_than = int(self.older_than_entry.get())
            except ValueError:
                messagebox.showerror("Error", "Older than days must be a number")
                return
        
        self.result = FilterAction(
            name=name,
            file_types=file_types,
            name_contains=self.name_contains_entry.get().strip(),
            older_than_days=older_than,
            action_type=self.action_var.get(),
            destination=self.destination_entry.get().strip(),
            rename_pattern=self.rename_entry.get().strip(),
            priority=int(self.priority_slider.get())
        )
        
        self.destroy()


class ProgressWindow(ctk.CTkToplevel):
    """Progress window for organization operation"""
    
    def __init__(self, parent, organizer, dry_run=False):
        super().__init__(parent)
        
        self.title("Dry Run Progress" if dry_run else "Organization Progress")
        self.geometry("600x400")
        
        self.organizer = organizer
        self.dry_run = dry_run
        
        # Progress info
        ctk.CTkLabel(self, text="Processing files...",
                    font=("Arial", 14, "bold")).pack(pady=10)
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(self, width=500)
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)
        
        # Status label
        self.status_label = ctk.CTkLabel(self, text="Starting...")
        self.status_label.pack(pady=5)
        
        # Results text
        self.results_text = ctk.CTkTextbox(self, width=550, height=250)
        self.results_text.pack(padx=20, pady=10)
        
        # Close button
        self.close_btn = ctk.CTkButton(self, text="Close", state="disabled",
                                       command=self.destroy)
        self.close_btn.pack(pady=10)
    
    def start_organization(self):
        """Start the organization process"""
        # This would be run in a thread in production
        self.after(100, self.run_organization)
    
    def run_organization(self):
        """Run the actual organization"""
        results = self.organizer.organize()
        
        # Display results
        self.results_text.insert("1.0", results)
        self.progress_bar.set(1.0)
        self.status_label.configure(text="Complete!")
        self.close_btn.configure(state="normal")


class FolderOrganizer:
    """Main organization engine"""
    
    def __init__(self, target_folder, folder_rules, filter_actions, settings, dry_run=False):
        self.target_folder = target_folder
        self.folder_rules = folder_rules
        self.filter_actions = filter_actions
        self.settings = settings
        self.dry_run = dry_run
        self.log = []
    
    def organize(self):
        """Main organization method"""
        if self.dry_run:
            return self.generate_dry_run_report()
        else:
            return self.perform_organization()
    
    def generate_dry_run_report(self):
        """Generate dry run report"""
        report = "DRY RUN REPORT\n" + "="*50 + "\n\n"
        report += f"Target folder: {self.target_folder}\n\n"
        
        # Analyze files
        files_to_move = []
        folders_to_create = set()
        
        for root, dirs, files in os.walk(self.target_folder):
            # Skip if this is already an organized folder
            if self.settings.exclude_organized_folders:
                if any(rule.folder_name in root for rule in self.folder_rules if not rule.is_time_based):
                    continue
            
            for file in files:
                file_path = os.path.join(root, file)
                
                # Check exclusions
                if self.is_excluded(file):
                    continue
                
                # Check filters first
                filter_result = self.apply_filters(file_path)
                if filter_result:
                    files_to_move.append((file_path, filter_result))
                    continue
                
                # Apply folder rules
                dest = self.get_destination(file_path)
                if dest and dest != root:
                    files_to_move.append((file_path, dest))
                    folders_to_create.add(dest)
        
        report += f"Files to move: {len(files_to_move)}\n"
        report += f"Folders to create: {len(folders_to_create)}\n\n"
        
        if files_to_move:
            report += "Sample moves (first 10):\n"
            for src, dest in files_to_move[:10]:
                report += f"  {os.path.basename(src)} → {dest}\n"
        
        return report
    
    def perform_organization(self):
        """Perform actual organization"""
        report = "ORGANIZATION COMPLETE\n" + "="*50 + "\n\n"
        
        moved_count = 0
        created_folders = set()
        errors = []
        
        # Create backup log if enabled
        if self.settings.create_backup_log:
            self.create_backup_log()
        
        for root, dirs, files in os.walk(self.target_folder):
            # Skip excluded folders
            if self.settings.exclude_organized_folders:
                if any(rule.folder_name in root for rule in self.folder_rules if not rule.is_time_based):
                    continue
            
            for file in files:
                file_path = os.path.join(root, file)
                
                # Check exclusions
                if self.is_excluded(file):
                    continue
                
                try:
                    # Check filters first
                    filter_result = self.apply_filters(file_path)
                    if filter_result:
                        if filter_result == "DELETE":
                            os.remove(file_path)
                            self.log.append(f"Deleted: {file_path}")
                        elif filter_result != "EXCLUDE":
                            self.move_file(file_path, filter_result)
                            moved_count += 1
                        continue
                    
                    # Apply folder rules
                    dest = self.get_destination(file_path)
                    if dest and dest != root:
                        # Create destination folder if needed
                        if not os.path.exists(dest):
                            os.makedirs(dest, exist_ok=True)
                            created_folders.add(dest)
                        
                        # Move file
                        self.move_file(file_path, dest)
                        moved_count += 1
                        
                except Exception as e:
                    errors.append(f"Error moving {file}: {str(e)}")
        
        report += f"Files moved: {moved_count}\n"
        report += f"Folders created: {len(created_folders)}\n"
        report += f"Errors: {len(errors)}\n\n"
        
        if errors:
            report += "Errors encountered:\n"
            for error in errors[:10]:
                report += f"  {error}\n"
        
        return report
    
    def is_excluded(self, filename):
        """Check if file should be excluded"""
        # Check exclude patterns
        for pattern in self.settings.exclude_files:
            if pattern in filename:
                return True
        
        # Check date exclusion
        if self.settings.exclude_before_date:
            try:
                exclude_date = datetime.strptime(self.settings.exclude_before_date, "%Y-%m-%d")
                file_date = datetime.fromtimestamp(os.path.getmtime(filename))
                if file_date < exclude_date:
                    return True
            except:
                pass
        
        return False
    
    def apply_filters(self, file_path):
        """Apply filters to file"""
        filename = os.path.basename(file_path)
        file_ext = os.path.splitext(filename)[1].lower()
        
        # Sort filters by priority
        sorted_filters = sorted(self.filter_actions, 
                               key=lambda f: f.priority, reverse=True)
        
        for filter_action in sorted_filters:
            if not filter_action.enabled:
                continue
            
            # Check conditions
            matches = True
            
            # Check file types
            if filter_action.file_types:
                if file_ext not in filter_action.file_types:
                    matches = False
            
            # Check name contains
            if matches and filter_action.name_contains:
                if filter_action.name_contains.lower() not in filename.lower():
                    matches = False
            
            # Check age
            if matches and filter_action.older_than_days:
                file_age = (datetime.now() - datetime.fromtimestamp(
                    os.path.getmtime(file_path))).days
                if file_age < filter_action.older_than_days:
                    matches = False
            
            if matches:
                # Apply action
                if filter_action.action_type == "delete":
                    return "DELETE"
                elif filter_action.action_type == "exclude":
                    return "EXCLUDE"
                elif filter_action.action_type in ["move", "move_external"]:
                    return filter_action.destination
                elif filter_action.action_type == "rename":
                    # Rename and continue processing
                    new_name = filter_action.rename_pattern.replace(
                        "{original}", os.path.splitext(filename)[0])
                    new_path = os.path.join(os.path.dirname(file_path), 
                                           new_name + file_ext)
                    if not self.dry_run:
                        os.rename(file_path, new_path)
                    return None
        
        return None
    
    def get_destination(self, file_path):
        """Get destination folder for file"""
        filename = os.path.basename(file_path)
        file_ext = os.path.splitext(filename)[1].lower()
        
        # Sort rules by hierarchy level
        sorted_rules = sorted(self.folder_rules, 
                            key=lambda r: r.hierarchy_level)
        
        dest_path = self.target_folder
        
        for level in range(1, 6):
            level_rules = [r for r in sorted_rules 
                          if r.hierarchy_level == level and r.enabled]
            
            for rule in level_rules:
                if rule.is_time_based:
                    # Get time-based folder name
                    file_date = datetime.fromtimestamp(
                        self.get_file_date(file_path, rule.date_source))
                    
                    if rule.time_pattern == "MMM":
                        folder_name = file_date.strftime("%b")
                    elif rule.time_pattern == "YYYY-MM":
                        folder_name = file_date.strftime("%Y-%m")
                    elif rule.time_pattern == "Weekly":
                        folder_name = file_date.strftime("Week_%W_%Y")
                    elif rule.time_pattern == "Daily":
                        folder_name = file_date.strftime("%Y-%m-%d")
                    else:  # Yearly
                        folder_name = file_date.strftime("%Y")
                    
                    dest_path = os.path.join(dest_path, folder_name)
                    break
                elif file_ext in rule.file_extensions:
                    dest_path = os.path.join(dest_path, rule.folder_name)
                    break
        
        return dest_path if dest_path != self.target_folder else None
    
    def get_file_date(self, file_path, date_source):
        """Get file date based on source"""
        if date_source == "created":
            return os.path.getctime(file_path)
        elif date_source == "accessed":
            return os.path.getatime(file_path)
        else:  # modified
            return os.path.getmtime(file_path)
    
    def move_file(self, src, dest_dir):
        """Move file to destination"""
        filename = os.path.basename(src)
        dest_path = os.path.join(dest_dir, filename)
        
        # Handle duplicates
        if os.path.exists(dest_path):
            if self.settings.delete_duplicates:
                # Keep newest
                if os.path.getmtime(src) > os.path.getmtime(dest_path):
                    os.remove(dest_path)
                else:
                    os.remove(src)
                    return
            else:
                # Rename with number
                base, ext = os.path.splitext(filename)
                counter = 1
                while os.path.exists(dest_path):
                    dest_path = os.path.join(dest_dir, f"{base}_{counter}{ext}")
                    counter += 1
        
        shutil.move(src, dest_path)
        self.log.append(f"Moved: {src} → {dest_path}")
    
    def create_backup_log(self):
        """Create backup log for restoration"""
        log_dir = self.settings.log_directory
        os.makedirs(log_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"backup_{timestamp}.json")
        
        backup_data = {
            "timestamp": timestamp,
            "target_folder": self.target_folder,
            "operations": self.log
        }
        
        with open(log_file, 'w') as f:
            json.dump(backup_data, f, indent=2)


def main():
    """Main entry point"""
    app = FolderOrganizerApp()
    app.mainloop()


if __name__ == "__main__":
    main()