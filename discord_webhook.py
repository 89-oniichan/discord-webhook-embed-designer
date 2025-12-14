"""
Discord Embed Designer 
A completely redesigned, modern, professional Discord webhook designer.

Features:
    - Modern tabbed interface with live preview
    - Visual color picker
    - Emoji selector
    - Template gallery
    - Auto-save & history
    - Keyboard shortcuts
    - Rich text editor
    - Export to multiple formats
    - Drag & drop field reordering
    - Beautiful premium UI
    - have to add bot functionallity in future 

Requirements:
    - Python 3.8+
    - customtkinter
    - pillow
    - requests
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
import json
import time
import requests
import urllib.request
import io
import logging
import os
from PIL import Image, ImageTk
from enum import Enum

# ============================================================================
# CONFIGURATION
# ============================================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Window Settings
WINDOW_WIDTH = 1600
WINDOW_HEIGHT = 950
MIN_WIDTH = 1200
MIN_HEIGHT = 750

# Colors - Premium Dark Theme
PREMIUM_BG = "#0a0e1a"
PREMIUM_CARD = "#131824"
PREMIUM_CARD_HOVER = "#1a1f2e"
PREMIUM_ACCENT = "#5865f2"
PREMIUM_ACCENT_HOVER = "#4752c4"
PREMIUM_SUCCESS = "#3ba55c"
PREMIUM_WARNING = "#faa61a"
PREMIUM_DANGER = "#ed4245"
PREMIUM_TEXT = "#ffffff"
PREMIUM_TEXT_DIM = "#b9bbbe"
PREMIUM_BORDER = "#1f2937"

# Discord Limits
MAX_TITLE = 256
MAX_DESC = 4096
MAX_FIELDS = 25
MAX_FIELD_NAME = 256
MAX_FIELD_VALUE = 1024
MAX_FOOTER = 2048
MAX_AUTHOR = 256

# Auto-save settings
AUTO_SAVE_INTERVAL = 30000  # 30 seconds
HISTORY_FILE = "embed_history.json"  # create a folder and save all data there {reminder imp}
TEMPLATES_FILE = "templates.json"
WEBHOOK_SETTINGS_FILE = "webhook_settings.json"

# Emoji Sets
EMOJI_COMMON = [
    "✅", "❌", "⚠️", "ℹ️", "🎉", "🎊", "🎈", "🎁", "🎮", "🎯",
    "🔥", "💯", "⭐", "🌟", "💎", "👑", "🏆", "🥇", "🥈", "🥉",
    "❤️", "💙", "💚", "💛", "🧡", "💜", "🖤", "🤍", "🤎", "💗",
    "👍", "👎", "👌", "✌️", "🤞", "🤝", "👏", "🙌", "💪", "🦾",
    "🚀", "🛸", "🎨", "🎭", "🎪", "🎬", "🎤", "🎧", "🎼", "🎹"
]

# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class EmbedField:
    """Embed field with validation."""
    name: str
    value: str
    inline: bool = False

    def validate(self) -> List[str]:
        errors = []
        if not self.name.strip():
            errors.append("Field name cannot be empty")
        if len(self.name) > MAX_FIELD_NAME:
            errors.append(f"Field name too long ({len(self.name)}/{MAX_FIELD_NAME})")
        if not self.value.strip():
            errors.append("Field value cannot be empty")
        if len(self.value) > MAX_FIELD_VALUE:
            errors.append(f"Field value too long ({len(self.value)}/{MAX_FIELD_VALUE})")
        return errors


@dataclass
class Embed:
    """Discord embed model."""
    title: str = ""
    description: str = ""
    color: str = "#5865F2"
    url: str = ""
    footer: str = ""
    footer_icon: str = ""
    author: str = ""
    author_icon: str = ""
    author_url: str = ""
    thumbnail: str = ""
    image: str = ""
    timestamp: bool = False
    fields: List[EmbedField] = field(default_factory=list)

    def validate(self) -> List[str]:
        errors = []
        if self.title and len(self.title) > MAX_TITLE:
            errors.append(f"Title too long ({len(self.title)}/{MAX_TITLE})")
        if self.description and len(self.description) > MAX_DESC:
            errors.append(f"Description too long ({len(self.description)}/{MAX_DESC})")
        if self.footer and len(self.footer) > MAX_FOOTER:
            errors.append(f"Footer too long ({len(self.footer)}/{MAX_FOOTER})")
        if self.author and len(self.author) > MAX_AUTHOR:
            errors.append(f"Author too long ({len(self.author)}/{MAX_AUTHOR})")
        if len(self.fields) > MAX_FIELDS:
            errors.append(f"Too many fields ({len(self.fields)}/{MAX_FIELDS})")

        for i, f in enumerate(self.fields):
            field_errors = f.validate()
            for err in field_errors:
                errors.append(f"Field {i+1}: {err}")

        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert to Discord API format."""
        result = {}

        if self.title:
            result["title"] = self.title
        if self.description:
            result["description"] = self.description
        # Only include URL if it's valid (starts with http:// or https://)
        if self.url and (self.url.startswith('http://') or self.url.startswith('https://')):
            result["url"] = self.url
        if self.color:
            result["color"] = int(self.color.lstrip('#'), 16) if self.color.startswith('#') else 0

        if self.footer or self.footer_icon:
            result["footer"] = {}
            if self.footer:
                result["footer"]["text"] = self.footer
            if self.footer_icon and (self.footer_icon.startswith('http://') or self.footer_icon.startswith('https://')):
                result["footer"]["icon_url"] = self.footer_icon

        if self.author or self.author_icon or self.author_url:
            result["author"] = {}
            if self.author:
                result["author"]["name"] = self.author
            if self.author_icon and (self.author_icon.startswith('http://') or self.author_icon.startswith('https://')):
                result["author"]["icon_url"] = self.author_icon
            if self.author_url and (self.author_url.startswith('http://') or self.author_url.startswith('https://')):
                result["author"]["url"] = self.author_url

        if self.thumbnail and (self.thumbnail.startswith('http://') or self.thumbnail.startswith('https://')):
            result["thumbnail"] = {"url": self.thumbnail}
        if self.image and (self.image.startswith('http://') or self.image.startswith('https://')):
            result["image"] = {"url": self.image}

        if self.timestamp:
            result["timestamp"] = datetime.utcnow().isoformat()

        if self.fields:
            result["fields"] = [
                {"name": f.name, "value": f.value, "inline": f.inline}
                for f in self.fields
            ]

        return result


@dataclass
class MessageButton:
    """Discord message button component."""
    label: str
    url: str = ""  # For link buttons
    style: str = "primary"  # primary, secondary, success, danger, link
    emoji: str = ""
    disabled: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to Discord API format."""
        result = {"type": 2}  # Type 2 = Button

        if self.label:
            result["label"] = self.label

        if self.style == "link" and self.url:
            result["style"] = 5  # Link button
            result["url"] = self.url
        else:
            # Style mapping: primary=1, secondary=2, success=3, danger=4
            style_map = {"primary": 1, "secondary": 2, "success": 3, "danger": 4}
            result["style"] = style_map.get(self.style, 1)
            result["custom_id"] = f"btn_{self.label.lower().replace(' ', '_')}"

        # Only add emoji if it's actually set and not empty
        if self.emoji and self.emoji.strip():
            result["emoji"] = {"name": self.emoji}

        if self.disabled:
            result["disabled"] = True

        return result

    def validate(self) -> List[str]:
        """Validate button."""
        errors = []
        if not self.label:
            errors.append("Button label is required")
        if len(self.label) > 80:
            errors.append(f"Button label too long ({len(self.label)}/80)")
        if self.style == "link" and not self.url:
            errors.append("Link buttons require a URL")
        return errors


@dataclass
class SelectOption:
    """Select menu option."""
    label: str
    value: str
    description: str = ""
    emoji: str = ""
    default: bool = False  # Mark as default/recommended option

    def to_dict(self) -> Dict[str, Any]:
        """Convert to Discord API format."""
        result = {"label": self.label, "value": self.value}
        if self.description:
            result["description"] = self.description
        if self.emoji:
            result["emoji"] = {"name": self.emoji}
        if self.default:
            result["default"] = True
        return result


@dataclass
class SelectMenu:
    """Discord select menu component."""
    placeholder: str = "Select an option"
    options: List[SelectOption] = field(default_factory=list)
    min_values: int = 1
    max_values: int = 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to Discord API format."""
        return {
            "type": 3,  # Type 3 = Select Menu
            "custom_id": "select_menu",
            "placeholder": self.placeholder,
            "min_values": self.min_values,
            "max_values": self.max_values,
            "options": [opt.to_dict() for opt in self.options]
        }

    def validate(self) -> List[str]:
        """Validate select menu."""
        errors = []
        if not self.options:
            errors.append("Select menu must have at least one option")
        if len(self.options) > 25:
            errors.append(f"Too many options ({len(self.options)}/25)")
        return errors


# ============================================================================
# PREMIUM UI COMPONENTS
# ============================================================================

class PremiumButton(ctk.CTkButton):
    """Premium styled button with hover effects."""

    def __init__(self, master, **kwargs):
        # Set premium defaults
        defaults = {
            "corner_radius": 8,
            "font": ("Segoe UI", 13, "bold"),
            "height": 38,
            "fg_color": PREMIUM_ACCENT,
            "hover_color": PREMIUM_ACCENT_HOVER,
        }
        defaults.update(kwargs)
        super().__init__(master, **defaults)


class PremiumEntry(ctk.CTkEntry):
    """Premium styled entry with validation."""

    def __init__(self, master, **kwargs):
        defaults = {
            "corner_radius": 8,
            "font": ("Segoe UI", 12),
            "height": 40,
            "border_width": 2,
            "border_color": PREMIUM_BORDER,
        }
        defaults.update(kwargs)
        super().__init__(master, **defaults)


class PremiumTextbox(ctk.CTkTextbox):
    """Premium styled textbox."""

    def __init__(self, master, **kwargs):
        defaults = {
            "corner_radius": 8,
            "font": ("Segoe UI", 12),
            "border_width": 2,
            "border_color": PREMIUM_BORDER,
        }
        defaults.update(kwargs)
        super().__init__(master, **defaults)


class ColorPickerButton(ctk.CTkButton):
    """Custom color picker button with preview."""

    def __init__(self, master, initial_color="#5865F2", callback=None):
        self.current_color = initial_color
        self.callback = callback

        super().__init__(
            master,
            text="",
            width=80,
            height=40,
            corner_radius=8,
            fg_color=initial_color,
            hover_color=initial_color,
            command=self.pick_color
        )
        self.update_color(initial_color)

    def pick_color(self):
        color = colorchooser.askcolor(
            title="Choose Color",
            initialcolor=self.current_color
        )
        if color[1]:
            self.update_color(color[1])
            if self.callback:
                self.callback(color[1])

    def update_color(self, color: str):
        self.current_color = color
        self.configure(fg_color=color, hover_color=color)
        # Add checkered pattern for better visibility
        self.configure(text="🎨")


class EmojiPicker(ctk.CTkToplevel):
    """Premium emoji picker dialog."""

    def __init__(self, parent, callback):
        super().__init__(parent)
        self.callback = callback

        self.title("Emoji Picker")
        self.geometry("500x400")
        self.resizable(False, False)
        self.grab_set()

        # Title
        title_label = ctk.CTkLabel(
            self,
            text="Select an Emoji",
            font=("Segoe UI", 20, "bold")
        )
        title_label.pack(pady=20)

        # Emoji grid
        grid_frame = ctk.CTkScrollableFrame(self, width=460, height=280)
        grid_frame.pack(padx=20, pady=10, fill="both", expand=True)

        row, col = 0, 0
        for emoji in EMOJI_COMMON:
            btn = ctk.CTkButton(
                grid_frame,
                text=emoji,
                width=50,
                height=50,
                font=("Segoe UI", 24),
                fg_color="transparent",
                hover_color=PREMIUM_CARD_HOVER,
                command=lambda e=emoji: self.select_emoji(e)
            )
            btn.grid(row=row, column=col, padx=5, pady=5)

            col += 1
            if col >= 8:
                col = 0
                row += 1

    def select_emoji(self, emoji):
        self.callback(emoji)
        self.destroy()


class FieldCard(ctk.CTkFrame):
    """Premium field card with inline editing."""

    def __init__(self, master, field: EmbedField, on_edit, on_delete, on_move_up, on_move_down):
        super().__init__(master, fg_color=PREMIUM_CARD, corner_radius=12, height=80)
        self.pack_propagate(False)

        self.field = field
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.on_move_up = on_move_up
        self.on_move_down = on_move_down

        self.pack(fill="x", padx=10, pady=5)

        # Main content
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=12, pady=10)

        # Left side - Field info
        info_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True)

        # Top row: Name and inline badge
        top_row = ctk.CTkFrame(info_frame, fg_color="transparent")
        top_row.pack(fill="x", anchor="w")

        name_label = ctk.CTkLabel(
            top_row,
            text=field.name[:50] + ("..." if len(field.name) > 50 else ""),
            font=("Segoe UI", 12, "bold"),
            text_color=PREMIUM_TEXT,
            anchor="w"
        )
        name_label.pack(side="left")

        if field.inline:
            inline_badge = ctk.CTkLabel(
                top_row,
                text="Inline",
                font=("Segoe UI", 9),
                text_color=PREMIUM_ACCENT,
                fg_color=PREMIUM_CARD_HOVER,
                corner_radius=4,
                padx=6,
                pady=2
            )
            inline_badge.pack(side="left", padx=(8, 0))

        # Value preview
        value_preview = field.value[:100] + ("..." if len(field.value) > 100 else "")
        value_label = ctk.CTkLabel(
            info_frame,
            text=value_preview,
            font=("Segoe UI", 10),
            text_color=PREMIUM_TEXT_DIM,
            anchor="w",
            wraplength=400
        )
        value_label.pack(anchor="w", pady=(4, 0))

        # Right side - Action buttons (vertical stack)
        action_frame = ctk.CTkFrame(content_frame, fg_color="transparent", width=120)
        action_frame.pack(side="right", fill="y", padx=(10, 0))
        action_frame.pack_propagate(False)

        # Top row buttons
        top_buttons = ctk.CTkFrame(action_frame, fg_color="transparent")
        top_buttons.pack(side="top", fill="x")

        ctk.CTkButton(
            top_buttons,
            text="⬆️",
            width=40,
            height=28,
            fg_color=PREMIUM_CARD_HOVER,
            hover_color=PREMIUM_BORDER,
            command=on_move_up,
            font=("Segoe UI", 14)
        ).pack(side="left", padx=(0, 3))

        ctk.CTkButton(
            top_buttons,
            text="⬇️",
            width=40,
            height=28,
            fg_color=PREMIUM_CARD_HOVER,
            hover_color=PREMIUM_BORDER,
            command=on_move_down,
            font=("Segoe UI", 14)
        ).pack(side="left")

        # Bottom row buttons
        bottom_buttons = ctk.CTkFrame(action_frame, fg_color="transparent")
        bottom_buttons.pack(side="top", fill="x", pady=(6, 0))

        ctk.CTkButton(
            bottom_buttons,
            text="✏️ Edit",
            width=55,
            height=28,
            fg_color=PREMIUM_ACCENT,
            hover_color=PREMIUM_ACCENT_HOVER,
            command=on_edit,
            font=("Segoe UI", 10)
        ).pack(side="left", padx=(0, 3))

        ctk.CTkButton(
            bottom_buttons,
            text="🗑️",
            width=28,
            height=28,
            fg_color=PREMIUM_DANGER,
            hover_color="#c03537",
            command=on_delete,
            font=("Segoe UI", 12)
        ).pack(side="left")


# ============================================================================
# MAIN APPLICATION
# ============================================================================

class PremiumEmbedDesigner(ctk.CTk):
    """Premium Discord Embed Designer."""

    def __init__(self):
        super().__init__()

        # Window setup
        self.title("Discord Embed Designer - by oniisama")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(MIN_WIDTH, MIN_HEIGHT)

        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # State
        self.current_embed = Embed()
        self.history: List[Embed] = []
        self.templates: List[Dict] = []
        self.auto_save_id = None
        self.preview_theme = "dark"  # dark, light, amoled
        self.color_history: List[str] = ["#5865F2"]  # Recent colors
        self.validation_errors: List[str] = []

        # Webhook settings
        self.webhook_settings = {
            "url": "",
            "username": "",
            "avatar_url": ""
        }

        # Load saved data
        self.load_history()
        self.load_templates()
        self.load_webhook_settings()

        # Build UI
        self.build_ui()

        # Start auto-save
        self.start_auto_save()

        # Bind keyboard shortcuts
        self.bind_shortcuts()

    def build_ui(self):
        """Build the premium UI."""
        self.configure(fg_color=PREMIUM_BG)

        # Main container - reduced padding for more space
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=12, pady=12)

        # Top bar
        self.build_top_bar(main_container)

        # Content area (Editor + Preview)
        content_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, pady=(10, 0))

        # Left side - Editor (60%)
        editor_frame = ctk.CTkFrame(content_frame, fg_color=PREMIUM_CARD, corner_radius=16)
        editor_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        self.build_editor(editor_frame)

        # Right side - Preview (40%)
        preview_frame = ctk.CTkFrame(content_frame, fg_color=PREMIUM_CARD, corner_radius=16, width=500)
        preview_frame.pack(side="right", fill="both")
        preview_frame.pack_propagate(False)

        self.build_preview(preview_frame)

        # Status bar at bottom
        self.build_status_bar(main_container)

    def build_top_bar(self, parent):
        """Build top action bar."""
        top_bar = ctk.CTkFrame(parent, fg_color=PREMIUM_CARD, corner_radius=12, height=60)
        top_bar.pack(fill="x")
        top_bar.pack_propagate(False)

        # Left side - Title
        left_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        left_frame.pack(side="left", padx=15, pady=12)

        title_label = ctk.CTkLabel(
            left_frame,
            text="Discord Embed Designer",
            font=("Segoe UI", 20, "bold"),
            text_color=PREMIUM_TEXT
        )
        title_label.pack(side="left")

        version_label = ctk.CTkLabel(
            left_frame,
            text="by oniisama",
            font=("Segoe UI", 10, "bold"),
            text_color=PREMIUM_ACCENT,
            fg_color=PREMIUM_CARD_HOVER,
            corner_radius=4,
            padx=8,
            pady=3
        )
        version_label.pack(side="left", padx=(8, 0))

        # Right side - Actions
        right_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        right_frame.pack(side="right", padx=15, pady=12)

        PremiumButton(
            right_frame,
            text="🗑️ Clear",
            width=80,
            height=36,
            fg_color=PREMIUM_DANGER,
            hover_color="#c03537",
            command=self.clear_all
        ).pack(side="left", padx=4)

        PremiumButton(
            right_frame,
            text="📋 Templates",
            width=110,
            height=36,
            command=self.show_templates
        ).pack(side="left", padx=4)

        PremiumButton(
            right_frame,
            text="📜 History",
            width=100,
            height=36,
            command=self.show_history
        ).pack(side="left", padx=4)

        PremiumButton(
            right_frame,
            text="📤 Export",
            width=90,
            height=36,
            fg_color=PREMIUM_SUCCESS,
            hover_color="#2d8a47",
            command=self.show_export_menu
        ).pack(side="left", padx=4)

        PremiumButton(
            right_frame,
            text="🚀 Send",
            width=80,
            height=36,
            fg_color=PREMIUM_ACCENT,
            command=self.send_webhook
        ).pack(side="left", padx=4)

    def build_editor(self, parent):
        """Build tabbed editor interface."""
        # Tab view - directly at the top, no extra frame
        self.tab_view = ctk.CTkTabview(parent, fg_color="transparent", corner_radius=12)
        self.tab_view.pack(fill="both", expand=True, padx=15, pady=15)

        # Create tabs with clear names
        self.tab_view.add("Content")
        self.tab_view.add("Style")
        self.tab_view.add("Fields")
        self.tab_view.add("Images")

        # Build tab contents
        self.build_content_tab()
        self.build_style_tab()
        self.build_fields_tab()
        self.build_images_tab()

    def build_content_tab(self):
        """Build content editing tab."""
        tab = self.tab_view.tab("Content")

        # Container (no scroll, we want max space)
        container = ctk.CTkFrame(tab, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=10, pady=10)

        # Title section
        self.create_label(container, "Title", "Main heading of your embed", pady=(0, 3))
        self.title_entry = PremiumEntry(container, placeholder_text="Enter embed title...", height=50)
        self.title_entry.pack(fill="x", pady=(0, 3))

        # Character counter for title
        self.title_counter = ctk.CTkLabel(
            container,
            text=f"0 / {MAX_TITLE}",
            font=("Segoe UI", 9),
            text_color=PREMIUM_TEXT_DIM
        )
        self.title_counter.pack(anchor="e", pady=(0, 5))
        self.title_entry.bind("<KeyRelease>", lambda e: self.update_counter(self.title_entry, self.title_counter, MAX_TITLE))

        # URL section (right under title)
        self.create_label(container, "Title URL (Optional)", "Make the title clickable", pady=(3, 3))
        self.url_entry = PremiumEntry(container, placeholder_text="https://example.com", height=45)
        self.url_entry.pack(fill="x", pady=(0, 8))

        # Description section
        self.create_label(container, "Description", "Main content (supports markdown)", pady=(8, 3))

        # Markdown toolbar
        toolbar = ctk.CTkFrame(container, fg_color="transparent", height=35)
        toolbar.pack(fill="x", pady=(0, 5))
        toolbar.pack_propagate(False)

        toolbar_buttons = [
            ("**B**", "Bold", self.insert_bold),
            ("*I*", "Italic", self.insert_italic),
            ("`<>`", "Code", self.insert_code),
            ("🔗", "Link", self.insert_link),
            ("😀", "Emoji", self.insert_emoji),
            ("📋", "Inline Field", self.insert_inline_field),
        ]

        for text, tooltip, cmd in toolbar_buttons:
            btn = ctk.CTkButton(
                toolbar,
                text=text,
                width=55,
                height=32,
                fg_color=PREMIUM_CARD_HOVER,
                hover_color=PREMIUM_BORDER,
                command=cmd,
                font=("Segoe UI", 11)
            )
            btn.pack(side="left", padx=3)

        # Description text - MUCH LARGER
        self.desc_text = PremiumTextbox(container, height=400)
        self.desc_text.pack(fill="both", expand=True, pady=(0, 3))

        # Character counter for description
        self.desc_counter = ctk.CTkLabel(
            container,
            text=f"0 / {MAX_DESC}",
            font=("Segoe UI", 9),
            text_color=PREMIUM_TEXT_DIM
        )
        self.desc_counter.pack(anchor="e", pady=(0, 5))
        self.desc_text.bind("<KeyRelease>", lambda e: self.update_textbox_counter(self.desc_text, self.desc_counter, MAX_DESC))

    def build_style_tab(self):
        """Build style customization tab."""
        tab = self.tab_view.tab("Style")

        # Container with scroll
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        # Color section
        self.create_label(scroll, "Embed Color", "Color bar on the left side")

        color_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        color_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.color_picker = ColorPickerButton(
            color_frame,
            initial_color="#5865F2",
            callback=self.on_color_change
        )
        self.color_picker.pack(side="left", padx=(0, 10))

        self.color_entry = PremiumEntry(
            color_frame,
            placeholder_text="#5865F2",
            width=200
        )
        self.color_entry.pack(side="left", fill="x", expand=True)
        self.color_entry.insert(0, "#5865F2")
        self.color_entry.bind("<KeyRelease>", self.on_color_entry_change)

        # Preset colors
        self.create_label(scroll, "Quick Colors", pady=(15, 5))

        preset_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        preset_frame.pack(fill="x", padx=10, pady=(0, 10))

        preset_colors = [
            ("#5865F2", "Blurple"),
            ("#3BA55C", "Green"),
            ("#ED4245", "Red"),
            ("#FAA61A", "Yellow"),
            ("#EB459E", "Pink"),
            ("#9B59B6", "Purple"),
        ]

        for color, name in preset_colors:
            btn = ctk.CTkButton(
                preset_frame,
                text="",
                width=60,
                height=35,
                fg_color=color,
                hover_color=color,
                corner_radius=8,
                command=lambda c=color: self.set_color(c)
            )
            btn.pack(side="left", padx=3)

        # Color history section
        self.create_label(scroll, "Recent Colors", "Your recently used colors", pady=(15, 5))

        self.color_history_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self.color_history_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.refresh_color_history()

        # Author section
        self.create_label(scroll, "Author", "Shows at the top of the embed", pady=(20, 5))

        self.author_entry = PremiumEntry(scroll, placeholder_text="Author name", height=40)
        self.author_entry.pack(fill="x", padx=10, pady=(0, 5))

        self.author_icon_entry = PremiumEntry(scroll, placeholder_text="Author icon URL (optional)", height=40)
        self.author_icon_entry.pack(fill="x", padx=10, pady=(0, 5))

        self.author_url_entry = PremiumEntry(scroll, placeholder_text="Author URL (optional)", height=40)
        self.author_url_entry.pack(fill="x", padx=10, pady=(0, 10))

        # Footer section
        self.create_label(scroll, "Footer", "Shows at the bottom of the embed", pady=(15, 5))

        self.footer_entry = PremiumEntry(scroll, placeholder_text="Footer text", height=40)
        self.footer_entry.pack(fill="x", padx=10, pady=(0, 5))

        # Footer counter
        self.footer_counter = ctk.CTkLabel(
            scroll,
            text=f"0 / {MAX_FOOTER}",
            font=("Segoe UI", 10),
            text_color=PREMIUM_TEXT_DIM
        )
        self.footer_counter.pack(anchor="e", padx=10, pady=(0, 5))
        self.footer_entry.bind("<KeyRelease>", lambda e: self.update_counter(self.footer_entry, self.footer_counter, MAX_FOOTER))

        self.footer_icon_entry = PremiumEntry(scroll, placeholder_text="Footer icon URL (optional)", height=40)
        self.footer_icon_entry.pack(fill="x", padx=10, pady=(0, 10))

        # Timestamp
        self.timestamp_var = tk.BooleanVar()
        timestamp_check = ctk.CTkCheckBox(
            scroll,
            text="Include current timestamp",
            variable=self.timestamp_var,
            font=("Segoe UI", 12),
            checkbox_width=24,
            checkbox_height=24,
            corner_radius=6
        )
        timestamp_check.pack(anchor="w", padx=10, pady=(10, 0))

    def build_fields_tab(self):
        """Build fields management tab."""
        tab = self.tab_view.tab("Fields")

        # Header
        header_frame = ctk.CTkFrame(tab, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=(10, 15))

        ctk.CTkLabel(
            header_frame,
            text="Embed Fields",
            font=("Segoe UI", 16, "bold"),
            text_color=PREMIUM_TEXT
        ).pack(side="left")

        self.field_count_label = ctk.CTkLabel(
            header_frame,
            text="0 / 25",
            font=("Segoe UI", 12),
            text_color=PREMIUM_TEXT_DIM
        )
        self.field_count_label.pack(side="left", padx=(10, 0))

        PremiumButton(
            header_frame,
            text="+ Add Field",
            width=130,
            height=35,
            command=self.add_field_dialog
        ).pack(side="right")

        # Fields list
        self.fields_container = ctk.CTkScrollableFrame(
            tab,
            fg_color="transparent"
        )
        self.fields_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.refresh_fields_list()

    def build_images_tab(self):
        """Build images tab."""
        tab = self.tab_view.tab("Images")

        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # Thumbnail
        self.create_label(scroll, "Thumbnail", "Small image in top-right corner")
        self.thumbnail_entry = PremiumEntry(scroll, placeholder_text="Thumbnail image URL", height=40)
        self.thumbnail_entry.pack(fill="x", padx=10, pady=(0, 10))

        # Image
        self.create_label(scroll, "Main Image", "Large image in the embed", pady=(15, 5))
        self.image_entry = PremiumEntry(scroll, placeholder_text="Main image URL", height=40)
        self.image_entry.pack(fill="x", padx=10, pady=(0, 10))

        # Image tips
        tips_frame = ctk.CTkFrame(scroll, fg_color=PREMIUM_CARD_HOVER, corner_radius=12)
        tips_frame.pack(fill="x", padx=10, pady=(20, 10))

        ctk.CTkLabel(
            tips_frame,
            text="💡 Image Tips",
            font=("Segoe UI", 13, "bold"),
            text_color=PREMIUM_ACCENT
        ).pack(anchor="w", padx=15, pady=(10, 5))

        tips = [
            "• Use direct image URLs (ending in .png, .jpg, .gif)",
            "• Recommended: HTTPS URLs only",
            "• Thumbnail: Best at ~80x80 pixels",
            "• Main image: Best at 400-600px wide",
            "• Image hosts: Imgur, Discord CDN, etc."
        ]

        for tip in tips:
            ctk.CTkLabel(
                tips_frame,
                text=tip,
                font=("Segoe UI", 11),
                text_color=PREMIUM_TEXT_DIM,
                anchor="w"
            ).pack(anchor="w", padx=15, pady=2)

        ctk.CTkLabel(tips_frame, text="").pack(pady=5)

    def build_components_tab(self):
        """Build components tab for buttons and select menus."""
        tab = self.tab_view.tab("Components")

        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # Info header
        info_frame = ctk.CTkFrame(scroll, fg_color=PREMIUM_CARD_HOVER, corner_radius=12)
        info_frame.pack(fill="x", padx=10, pady=(0, 15))

        ctk.CTkLabel(
            info_frame,
            text="Interactive Components",
            font=("Segoe UI", 14, "bold"),
            text_color=PREMIUM_ACCENT
        ).pack(anchor="w", padx=15, pady=(12, 5))

        ctk.CTkLabel(
            info_frame,
            text="Add clickable buttons and dropdown menus below your embed",
            font=("Segoe UI", 10),
            text_color=PREMIUM_TEXT_DIM
        ).pack(anchor="w", padx=15, pady=(0, 12))

        # Webhook limitation warning
        warning_frame = ctk.CTkFrame(scroll, fg_color=PREMIUM_WARNING, corner_radius=12)
        warning_frame.pack(fill="x", padx=10, pady=(0, 15))

        ctk.CTkLabel(
            warning_frame,
            text="⚠️ Webhook Limitation",
            font=("Segoe UI", 12, "bold"),
            text_color="#000000"
        ).pack(anchor="w", padx=15, pady=(10, 3))

        ctk.CTkLabel(
            warning_frame,
            text="Only LINK buttons work with webhooks. Other button types and select menus require a Discord bot.",
            font=("Segoe UI", 10),
            text_color="#000000",
            wraplength=550,
            justify="left"
        ).pack(anchor="w", padx=15, pady=(0, 10))

        # Buttons section
        buttons_header = ctk.CTkFrame(scroll, fg_color="transparent")
        buttons_header.pack(fill="x", padx=10, pady=(10, 8))

        ctk.CTkLabel(
            buttons_header,
            text="Buttons",
            font=("Segoe UI", 14, "bold"),
            text_color=PREMIUM_TEXT
        ).pack(side="left")

        ctk.CTkLabel(
            buttons_header,
            text=f"{len(self.buttons)}/5",
            font=("Segoe UI", 11),
            text_color=PREMIUM_TEXT_DIM
        ).pack(side="left", padx=(8, 0))

        PremiumButton(
            buttons_header,
            text="+ Add Button",
            width=130,
            height=32,
            command=self.add_button_dialog
        ).pack(side="right")

        # Buttons list container
        self.buttons_container = ctk.CTkFrame(scroll, fg_color="transparent")
        self.buttons_container.pack(fill="x", padx=10, pady=(0, 20))
        self.refresh_buttons_list()

        # Select Menus section
        menus_header = ctk.CTkFrame(scroll, fg_color="transparent")
        menus_header.pack(fill="x", padx=10, pady=(20, 8))

        ctk.CTkLabel(
            menus_header,
            text="Select Menus",
            font=("Segoe UI", 14, "bold"),
            text_color=PREMIUM_TEXT
        ).pack(side="left")

        ctk.CTkLabel(
            menus_header,
            text=f"{len(self.select_menus)}/1",
            font=("Segoe UI", 11),
            text_color=PREMIUM_TEXT_DIM
        ).pack(side="left", padx=(8, 0))

        PremiumButton(
            menus_header,
            text="+ Add Menu",
            width=130,
            height=32,
            command=self.add_select_menu_dialog
        ).pack(side="right")

        # Select menus list container
        self.menus_container = ctk.CTkFrame(scroll, fg_color="transparent")
        self.menus_container.pack(fill="x", padx=10, pady=(0, 10))
        self.refresh_menus_list()

        # Component tips
        tips_frame = ctk.CTkFrame(scroll, fg_color=PREMIUM_CARD_HOVER, corner_radius=12)
        tips_frame.pack(fill="x", padx=10, pady=(20, 10))

        ctk.CTkLabel(
            tips_frame,
            text="💡 Component Tips",
            font=("Segoe UI", 13, "bold"),
            text_color=PREMIUM_ACCENT
        ).pack(anchor="w", padx=15, pady=(10, 5))

        tips = [
            "• Buttons: Max 5 per row (use Link style for URLs)",
            "• Select Menus: Max 1 per message, up to 25 options",
            "• Link buttons open URLs, others are for bot interactions",
            "• Components appear below the embed in Discord",
            "• Note: Non-link buttons won't work without a bot backend"
        ]

        for tip in tips:
            ctk.CTkLabel(
                tips_frame,
                text=tip,
                font=("Segoe UI", 11),
                text_color=PREMIUM_TEXT_DIM,
                anchor="w"
            ).pack(anchor="w", padx=15, pady=2)

        ctk.CTkLabel(tips_frame, text="").pack(pady=5)

    def build_preview(self, parent):
        """Build live preview panel."""
        # Header
        header = ctk.CTkFrame(parent, fg_color="transparent", height=50)
        header.pack(fill="x", padx=15, pady=(10, 5))
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text="Live Preview",
            font=("Segoe UI", 16, "bold"),
            text_color=PREMIUM_TEXT
        ).pack(side="left")

        # Preview theme toggles
        theme_frame = ctk.CTkFrame(header, fg_color="transparent")
        theme_frame.pack(side="right", padx=(0, 5))

        for theme in ["Dark", "Light", "AMOLED"]:
            ctk.CTkButton(
                theme_frame,
                text=theme,
                width=65,
                height=30,
                fg_color=PREMIUM_ACCENT if self.preview_theme == theme.lower() else PREMIUM_CARD_HOVER,
                hover_color=PREMIUM_ACCENT_HOVER,
                command=lambda t=theme.lower(): self.set_preview_theme(t),
                font=("Segoe UI", 10)
            ).pack(side="left", padx=2)

        PremiumButton(
            header,
            text="🔄",
            width=35,
            height=30,
            command=self.update_preview
        ).pack(side="right", padx=(0, 5))

        # Preview canvas
        canvas_frame = ctk.CTkFrame(parent, fg_color=PREMIUM_BG, corner_radius=12)
        canvas_frame.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        self.preview_canvas = tk.Canvas(
            canvas_frame,
            bg="#36393f",
            highlightthickness=0,
            bd=0
        )
        self.preview_canvas.pack(fill="both", expand=True, padx=8, pady=8)

        # Auto-update on tab change
        self.tab_view.configure(command=lambda: self.after(100, self.update_preview))

        # Initial preview
        self.after(500, self.update_preview)

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def create_label(self, parent, text, subtitle="", pady=(5, 3)):
        """Create a styled label with optional subtitle."""
        label = ctk.CTkLabel(
            parent,
            text=text,
            font=("Segoe UI", 13, "bold"),
            text_color=PREMIUM_TEXT,
            anchor="w"
        )
        label.pack(anchor="w", pady=pady)

        if subtitle:
            sub = ctk.CTkLabel(
                parent,
                text=subtitle,
                font=("Segoe UI", 9),
                text_color=PREMIUM_TEXT_DIM,
                anchor="w"
            )
            sub.pack(anchor="w", pady=(0, 3))

    def update_counter(self, entry, label, max_chars):
        """Update character counter for entry."""
        current = len(entry.get())
        label.configure(text=f"{current} / {max_chars}")
        if current > max_chars:
            label.configure(text_color=PREMIUM_DANGER)
        else:
            label.configure(text_color=PREMIUM_TEXT_DIM)

    def update_textbox_counter(self, textbox, label, max_chars):
        """Update character counter for textbox."""
        current = len(textbox.get("1.0", "end-1c"))
        label.configure(text=f"{current} / {max_chars}")
        if current > max_chars:
            label.configure(text_color=PREMIUM_DANGER)
        else:
            label.configure(text_color=PREMIUM_TEXT_DIM)

    # ========================================================================
    # COLOR PICKER
    # ========================================================================

    def on_color_change(self, color):
        """Handle color picker change."""
        self.color_entry.delete(0, "end")
        self.color_entry.insert(0, color)
        self.update_preview()

    def on_color_entry_change(self, event):
        """Handle manual color entry change."""
        color = self.color_entry.get().strip()
        if color.startswith('#') and len(color) == 7:
            try:
                int(color[1:], 16)
                self.color_picker.update_color(color)
                self.update_preview()
            except ValueError:
                pass

    def set_color(self, color):
        """Set color from preset."""
        self.color_entry.delete(0, "end")
        self.color_entry.insert(0, color)
        self.color_picker.update_color(color)
        self.add_color_to_history(color)
        self.update_preview()

    def add_color_to_history(self, color):
        """Add color to history (max 10)."""
        if color in self.color_history:
            self.color_history.remove(color)
        self.color_history.insert(0, color)
        self.color_history = self.color_history[:10]  # Keep last 10
        self.refresh_color_history()

    def refresh_color_history(self):
        """Refresh color history display."""
        if not hasattr(self, 'color_history_frame'):
            return

        # Clear existing
        for widget in self.color_history_frame.winfo_children():
            widget.destroy()

        # Add color buttons
        for i, color in enumerate(self.color_history[:10]):
            btn = ctk.CTkButton(
                self.color_history_frame,
                text="",
                width=50,
                height=30,
                fg_color=color,
                hover_color=color,
                corner_radius=6,
                command=lambda c=color: self.set_color(c)
            )
            btn.pack(side="left", padx=2)

    # ========================================================================
    # STATUS BAR
    # ========================================================================

    def build_status_bar(self, parent):
        """Build status bar at bottom."""
        status_bar = ctk.CTkFrame(parent, fg_color=PREMIUM_CARD, corner_radius=12, height=35)
        status_bar.pack(fill="x", pady=(8, 0))
        status_bar.pack_propagate(False)

        # Validation status
        self.status_validation = ctk.CTkLabel(
            status_bar,
            text="✅ Valid",
            font=("Segoe UI", 10),
            text_color=PREMIUM_SUCCESS
        )
        self.status_validation.pack(side="left", padx=12)

        # Title stats
        self.status_title = ctk.CTkLabel(
            status_bar,
            text="Title: 0/256",
            font=("Segoe UI", 9),
            text_color=PREMIUM_TEXT_DIM
        )
        self.status_title.pack(side="left", padx=8)

        # Description stats
        self.status_desc = ctk.CTkLabel(
            status_bar,
            text="Description: 0/4096",
            font=("Segoe UI", 9),
            text_color=PREMIUM_TEXT_DIM
        )
        self.status_desc.pack(side="left", padx=8)

        # Fields stats
        self.status_fields = ctk.CTkLabel(
            status_bar,
            text="Fields: 0/25",
            font=("Segoe UI", 9),
            text_color=PREMIUM_TEXT_DIM
        )
        self.status_fields.pack(side="left", padx=8)

        # Auto-save status
        self.status_autosave = ctk.CTkLabel(
            status_bar,
            text="Auto-saved",
            font=("Segoe UI", 9),
            text_color=PREMIUM_TEXT_DIM
        )
        self.status_autosave.pack(side="right", padx=12)

    def update_status_bar(self):
        """Update status bar with current stats."""
        if not hasattr(self, 'status_validation'):
            return

        # Get current stats
        title_len = len(self.title_entry.get())
        desc_len = len(self.desc_text.get("1.0", "end-1c"))
        fields_count = len(self.current_embed.fields)

        # Update labels
        self.status_title.configure(
            text=f"Title: {title_len}/256",
            text_color=PREMIUM_DANGER if title_len > MAX_TITLE else PREMIUM_TEXT_DIM
        )

        self.status_desc.configure(
            text=f"Description: {desc_len}/4096",
            text_color=PREMIUM_DANGER if desc_len > MAX_DESC else PREMIUM_TEXT_DIM
        )

        self.status_fields.configure(
            text=f"Fields: {fields_count}/25",
            text_color=PREMIUM_WARNING if fields_count > 20 else PREMIUM_TEXT_DIM
        )

        # Validation status
        self.sync_embed_from_ui()
        errors = self.current_embed.validate()
        if errors:
            self.status_validation.configure(
                text=f"⚠️ {len(errors)} Error(s)",
                text_color=PREMIUM_WARNING
            )
            self.validation_errors = errors
        else:
            self.status_validation.configure(
                text="✅ Valid",
                text_color=PREMIUM_SUCCESS
            )
            self.validation_errors = []

    # ========================================================================
    # PREVIEW THEME
    # ========================================================================

    def set_preview_theme(self, theme):
        """Set preview theme (dark, light, amoled)."""
        self.preview_theme = theme
        self.update_preview()

    # ========================================================================
    # CLEAR ALL
    # ========================================================================

    def clear_all(self):
        """Clear all fields and reset to default."""
        if not messagebox.askyesno(
            "Clear All",
            "Clear all fields and start fresh?\n\nThis will reset the current embed."
        ):
            return

        # Reset embed
        self.current_embed = Embed()

        # Clear UI
        self.title_entry.delete(0, "end")
        self.desc_text.delete("1.0", "end")
        self.url_entry.delete(0, "end")
        self.color_entry.delete(0, "end")
        self.color_entry.insert(0, "#5865F2")
        self.author_entry.delete(0, "end")
        self.author_icon_entry.delete(0, "end")
        self.author_url_entry.delete(0, "end")
        self.footer_entry.delete(0, "end")
        self.footer_icon_entry.delete(0, "end")
        self.thumbnail_entry.delete(0, "end")
        self.image_entry.delete(0, "end")
        self.timestamp_var.set(False)

        # Refresh
        self.refresh_fields_list()
        self.update_preview()
        self.update_status_bar()

        messagebox.showinfo("Cleared", "All fields cleared!")

    # ========================================================================
    # MARKDOWN TOOLBAR
    # ========================================================================

    def insert_bold(self):
        """Insert bold markdown."""
        self.wrap_text("**")

    def insert_italic(self):
        """Insert italic markdown."""
        self.wrap_text("*")

    def insert_code(self):
        """Insert code markdown."""
        self.wrap_text("`")

    def insert_link(self):
        """Insert link markdown."""
        url = ctk.CTkInputDialog(
            text="Enter URL:",
            title="Insert Link"
        ).get_input()

        if url:
            try:
                selected = self.desc_text.get("sel.first", "sel.last")
                text = selected if selected else "link"
            except:
                text = "link"

            self.desc_text.insert("insert", f"[{text}]({url})")

    def insert_emoji(self):
        """Open emoji picker."""
        EmojiPicker(self, lambda emoji: self.desc_text.insert("insert", emoji))

    def insert_inline_field(self):
        """Insert field-like formatted text into description."""
        # Create dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title("Insert Inline Field")
        dialog.geometry("550x450")
        dialog.grab_set()

        # Center dialog
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        # Content
        content = ctk.CTkFrame(dialog, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=20)

        # Info text
        ctk.CTkLabel(
            content,
            text="Add field-like formatting to your description",
            font=("Segoe UI", 11),
            text_color=PREMIUM_TEXT_DIM
        ).pack(anchor="w", pady=(0, 15))

        # Label/Name
        ctk.CTkLabel(content, text="Label", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 5))
        label_entry = PremiumEntry(content, placeholder_text="e.g., Server Status, Join Date, etc.")
        label_entry.pack(fill="x", pady=(0, 15))
        label_entry.focus()

        # Value
        ctk.CTkLabel(content, text="Value", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 5))
        value_text = PremiumTextbox(content, height=80)
        value_text.pack(fill="both", expand=True, pady=(0, 15))

        # Format options
        format_var = tk.StringVar(value="bold_colon")
        format_section = ctk.CTkFrame(content, fg_color="transparent")
        format_section.pack(fill="x", pady=(5, 20))

        ctk.CTkLabel(
            format_section,
            text="Format Style:",
            font=("Segoe UI", 13, "bold")
        ).pack(anchor="w", pady=(0, 8))

        # Option 1: Inline format
        opt1_frame = ctk.CTkFrame(format_section, fg_color="transparent")
        opt1_frame.pack(fill="x", pady=3)

        ctk.CTkRadioButton(
            opt1_frame,
            text="Inline (same line)",
            variable=format_var,
            value="bold_colon",
            font=("Segoe UI", 11)
        ).pack(side="left")

        ctk.CTkLabel(
            opt1_frame,
            text="Example: **Label:** Value",
            font=("Segoe UI", 9),
            text_color=PREMIUM_TEXT_DIM
        ).pack(side="left", padx=(10, 0))

        # Option 2: Block format
        opt2_frame = ctk.CTkFrame(format_section, fg_color="transparent")
        opt2_frame.pack(fill="x", pady=3)

        ctk.CTkRadioButton(
            opt2_frame,
            text="Block (separate lines)",
            variable=format_var,
            value="bold_newline",
            font=("Segoe UI", 11)
        ).pack(side="left")

        ctk.CTkLabel(
            opt2_frame,
            text="Example: **Label** (newline) Value",
            font=("Segoe UI", 9),
            text_color=PREMIUM_TEXT_DIM
        ).pack(side="left", padx=(10, 0))

        # Buttons
        btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        btn_frame.pack(fill="x")

        def insert():
            label = label_entry.get().strip()
            value = value_text.get("1.0", "end-1c").strip()

            if not label or not value:
                messagebox.showwarning("Required", "Both label and value are required", parent=dialog)
                return

            # Format based on selection
            if format_var.get() == "bold_colon":
                formatted = f"**{label}:** {value}"
            else:  # bold_newline
                formatted = f"**{label}**\n{value}"

            # Insert at cursor position
            self.desc_text.insert("insert", formatted)
            dialog.destroy()

        PremiumButton(btn_frame, text="Cancel", width=120, fg_color=PREMIUM_CARD_HOVER,
                     hover_color=PREMIUM_BORDER, command=dialog.destroy).pack(side="left")
        PremiumButton(btn_frame, text="Insert", width=120, command=insert).pack(side="right")

    def wrap_text(self, wrapper):
        """Wrap selected text."""
        try:
            selected = self.desc_text.get("sel.first", "sel.last")
            self.desc_text.delete("sel.first", "sel.last")
            self.desc_text.insert("insert", f"{wrapper}{selected}{wrapper}")
        except:
            self.desc_text.insert("insert", wrapper + wrapper)

    # ========================================================================
    # FIELDS MANAGEMENT
    # ========================================================================

    def add_field_dialog(self):
        """Show add field dialog."""
        if len(self.current_embed.fields) >= MAX_FIELDS:
            messagebox.showwarning("Limit Reached", f"Maximum {MAX_FIELDS} fields allowed")
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("Add Field")
        dialog.geometry("500x450")
        dialog.grab_set()

        # Center dialog
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        # Content
        content = ctk.CTkFrame(dialog, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=20)

        # Name
        ctk.CTkLabel(content, text="Field Name", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 5))
        name_entry = PremiumEntry(content, placeholder_text="Enter field name...", height=40)
        name_entry.pack(fill="x", pady=(0, 10))

        # Value
        ctk.CTkLabel(content, text="Field Value", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(10, 5))
        value_text = PremiumTextbox(content, height=150)
        value_text.pack(fill="both", expand=True, pady=(0, 10))

        # Inline checkbox
        inline_var = tk.BooleanVar()
        ctk.CTkCheckBox(
            content,
            text="Display inline (side-by-side with other inline fields)",
            variable=inline_var,
            font=("Segoe UI", 11)
        ).pack(anchor="w", pady=(5, 15))

        # Buttons
        btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        btn_frame.pack(fill="x")

        def add_field():
            name = name_entry.get().strip()
            value = value_text.get("1.0", "end-1c").strip()

            if not name:
                messagebox.showwarning("Required", "Field name is required", parent=dialog)
                return
            if not value:
                messagebox.showwarning("Required", "Field value is required", parent=dialog)
                return

            field = EmbedField(name=name, value=value, inline=inline_var.get())
            errors = field.validate()

            if errors:
                messagebox.showerror("Validation Error", "\n".join(errors), parent=dialog)
                return

            self.current_embed.fields.append(field)
            self.refresh_fields_list()
            self.update_preview()
            dialog.destroy()

        PremiumButton(btn_frame, text="Cancel", width=120, fg_color=PREMIUM_CARD_HOVER,
                     hover_color=PREMIUM_BORDER, command=dialog.destroy).pack(side="left")
        PremiumButton(btn_frame, text="Add Field", width=120, command=add_field).pack(side="right")

    def edit_field_dialog(self, index):
        """Show edit field dialog."""
        field = self.current_embed.fields[index]

        dialog = ctk.CTkToplevel(self)
        dialog.title("Edit Field")
        dialog.geometry("500x450")
        dialog.grab_set()

        # Center dialog
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        # Content
        content = ctk.CTkFrame(dialog, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=20)

        # Name
        ctk.CTkLabel(content, text="Field Name", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 5))
        name_entry = PremiumEntry(content, placeholder_text="Enter field name...", height=40)
        name_entry.insert(0, field.name)
        name_entry.pack(fill="x", pady=(0, 10))

        # Value
        ctk.CTkLabel(content, text="Field Value", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(10, 5))
        value_text = PremiumTextbox(content, height=150)
        value_text.insert("1.0", field.value)
        value_text.pack(fill="both", expand=True, pady=(0, 10))

        # Inline checkbox
        inline_var = tk.BooleanVar(value=field.inline)
        ctk.CTkCheckBox(
            content,
            text="Display inline (side-by-side with other inline fields)",
            variable=inline_var,
            font=("Segoe UI", 11)
        ).pack(anchor="w", pady=(5, 15))

        # Buttons
        btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        btn_frame.pack(fill="x")

        def save_field():
            name = name_entry.get().strip()
            value = value_text.get("1.0", "end-1c").strip()

            if not name or not value:
                messagebox.showwarning("Required", "Both name and value are required", parent=dialog)
                return

            new_field = EmbedField(name=name, value=value, inline=inline_var.get())
            errors = new_field.validate()

            if errors:
                messagebox.showerror("Validation Error", "\n".join(errors), parent=dialog)
                return

            self.current_embed.fields[index] = new_field
            self.refresh_fields_list()
            self.update_preview()
            dialog.destroy()

        PremiumButton(btn_frame, text="Cancel", width=120, fg_color=PREMIUM_CARD_HOVER,
                     hover_color=PREMIUM_BORDER, command=dialog.destroy).pack(side="left")
        PremiumButton(btn_frame, text="Save", width=120, command=save_field).pack(side="right")

    def delete_field(self, index):
        """Delete a field."""
        if messagebox.askyesno("Confirm", "Delete this field?"):
            del self.current_embed.fields[index]
            self.refresh_fields_list()
            self.update_preview()

    def move_field_up(self, index):
        """Move field up."""
        if index > 0:
            self.current_embed.fields[index], self.current_embed.fields[index-1] = \
                self.current_embed.fields[index-1], self.current_embed.fields[index]
            self.refresh_fields_list()
            self.update_preview()

    def move_field_down(self, index):
        """Move field down."""
        if index < len(self.current_embed.fields) - 1:
            self.current_embed.fields[index], self.current_embed.fields[index+1] = \
                self.current_embed.fields[index+1], self.current_embed.fields[index]
            self.refresh_fields_list()
            self.update_preview()

    def refresh_fields_list(self):
        """Refresh the fields list display."""
        # Clear container
        for widget in self.fields_container.winfo_children():
            widget.destroy()

        # Update counter
        count = len(self.current_embed.fields)
        self.field_count_label.configure(text=f"{count} / {MAX_FIELDS}")

        if count > MAX_FIELDS * 0.8:
            self.field_count_label.configure(text_color=PREMIUM_WARNING)
        else:
            self.field_count_label.configure(text_color=PREMIUM_TEXT_DIM)

        # Add fields
        if not self.current_embed.fields:
            empty_label = ctk.CTkLabel(
                self.fields_container,
                text="No fields added yet.\nClick 'Add Field' to get started!",
                font=("Segoe UI", 13),
                text_color=PREMIUM_TEXT_DIM
            )
            empty_label.pack(pady=50)
        else:
            for i, field in enumerate(self.current_embed.fields):
                FieldCard(
                    self.fields_container,
                    field,
                    on_edit=lambda idx=i: self.edit_field_dialog(idx),
                    on_delete=lambda idx=i: self.delete_field(idx),
                    on_move_up=lambda idx=i: self.move_field_up(idx),
                    on_move_down=lambda idx=i: self.move_field_down(idx)
                )

    # ========================================================================
    # COMPONENTS MANAGEMENT
    # ========================================================================

    def add_button_dialog(self):
        """Show add button dialog."""
        if len(self.buttons) >= 5:
            messagebox.showwarning("Limit Reached", "Maximum 5 buttons per row")
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("Add Button")
        dialog.geometry("550x600")
        dialog.grab_set()

        # Center dialog
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        # Content
        content = ctk.CTkFrame(dialog, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=20)

        # Button Label
        ctk.CTkLabel(content, text="Button Label", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 5))
        label_entry = PremiumEntry(content, placeholder_text="Click Me!")
        label_entry.pack(fill="x", pady=(0, 15))
        label_entry.focus()

        # Style
        ctk.CTkLabel(content, text="Button Style", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(5, 8))
        style_var = tk.StringVar(value="primary")

        styles = [
            ("Primary (Blue)", "primary", PREMIUM_ACCENT),
            ("Secondary (Gray)", "secondary", "#4e5058"),
            ("Success (Green)", "success", PREMIUM_SUCCESS),
            ("Danger (Red)", "danger", PREMIUM_DANGER),
            ("Link (URL)", "link", "#00aff4")
        ]

        for label, value, color in styles:
            frame = ctk.CTkFrame(content, fg_color="transparent")
            frame.pack(fill="x", pady=2)

            ctk.CTkRadioButton(
                frame,
                text=label,
                variable=style_var,
                value=value,
                font=("Segoe UI", 11)
            ).pack(side="left")

            # Color indicator
            ctk.CTkLabel(
                frame,
                text="█",
                font=("Segoe UI", 14),
                text_color=color
            ).pack(side="left", padx=(5, 0))

        # URL (for link buttons)
        ctk.CTkLabel(content, text="URL (Required for Link style)", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(15, 5))
        url_entry = PremiumEntry(content, placeholder_text="https://example.com")
        url_entry.pack(fill="x", pady=(0, 15))

        # Emoji (optional)
        ctk.CTkLabel(content, text="Emoji (Optional)", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(5, 5))
        emoji_entry = PremiumEntry(content, placeholder_text="😀")
        emoji_entry.pack(fill="x", pady=(0, 20))

        # Buttons
        btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        btn_frame.pack(fill="x")

        def add():
            label = label_entry.get().strip()
            url = url_entry.get().strip()
            style = style_var.get()
            emoji = emoji_entry.get().strip()

            if not label:
                messagebox.showwarning("Required", "Button label is required", parent=dialog)
                return

            if style == "link" and not url:
                messagebox.showwarning("Required", "URL is required for link buttons", parent=dialog)
                return

            button = MessageButton(label=label, url=url, style=style, emoji=emoji)
            errors = button.validate()

            if errors:
                messagebox.showerror("Validation Error", "\n".join(errors), parent=dialog)
                return

            self.buttons.append(button)
            self.refresh_buttons_list()
            dialog.destroy()

        PremiumButton(btn_frame, text="Cancel", width=120, fg_color=PREMIUM_CARD_HOVER,
                     hover_color=PREMIUM_BORDER, command=dialog.destroy).pack(side="left")
        PremiumButton(btn_frame, text="Add Button", width=120, command=add).pack(side="right")

    def add_select_menu_dialog(self):
        """Show add select menu dialog."""
        if len(self.select_menus) >= 1:
            messagebox.showwarning("Limit Reached", "Maximum 1 select menu per message")
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("Add Select Menu")
        dialog.geometry("600x550")
        dialog.grab_set()

        # Center dialog
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        # Content
        content = ctk.CTkFrame(dialog, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=20)

        # Placeholder
        ctk.CTkLabel(content, text="Placeholder Text", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 5))
        placeholder_entry = PremiumEntry(content, placeholder_text="Select an option...")
        placeholder_entry.pack(fill="x", pady=(0, 15))
        placeholder_entry.insert(0, "Select an option")

        # Options
        ctk.CTkLabel(content, text="Options (Add at least 1, max 25)", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(5, 8))

        options_list = []

        options_frame = ctk.CTkScrollableFrame(content, height=250, fg_color=PREMIUM_CARD_HOVER)
        options_frame.pack(fill="both", expand=True, pady=(0, 10))

        def add_option():
            if len(options_list) >= 25:
                messagebox.showwarning("Limit Reached", "Maximum 25 options", parent=dialog)
                return

            # Create option editor dialog
            opt_dialog = ctk.CTkToplevel(dialog)
            opt_dialog.title("Add Option")
            opt_dialog.geometry("500x440")
            opt_dialog.grab_set()

            # Center
            opt_dialog.update_idletasks()
            ox = dialog.winfo_x() + (dialog.winfo_width() // 2) - 250
            oy = dialog.winfo_y() + (dialog.winfo_height() // 2) - 190
            opt_dialog.geometry(f"+{ox}+{oy}")

            opt_content = ctk.CTkFrame(opt_dialog, fg_color="transparent")
            opt_content.pack(fill="both", expand=True, padx=20, pady=20)

            # Label (required)
            ctk.CTkLabel(opt_content, text="Label (Required)", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 5))
            label_entry = PremiumEntry(opt_content, placeholder_text="Option name")
            label_entry.pack(fill="x", pady=(0, 15))
            label_entry.focus()

            # Description (optional)
            ctk.CTkLabel(opt_content, text="Description (Optional)", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(5, 5))
            desc_text = PremiumTextbox(opt_content, height=80)
            desc_text.pack(fill="x", pady=(0, 15))

            # Emoji (optional)
            ctk.CTkLabel(opt_content, text="Emoji (Optional)", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(5, 5))
            emoji_entry = PremiumEntry(opt_content, placeholder_text="😀")
            emoji_entry.pack(fill="x", pady=(0, 15))

            # Default checkbox
            default_var = tk.BooleanVar(value=False)
            ctk.CTkCheckBox(
                opt_content,
                text="⭐ Mark as Default (Pre-selected option)",
                variable=default_var,
                font=("Segoe UI", 11)
            ).pack(anchor="w", pady=(5, 20))

            # Buttons
            opt_btn_frame = ctk.CTkFrame(opt_content, fg_color="transparent")
            opt_btn_frame.pack(fill="x")

            def save_option():
                label = label_entry.get().strip()
                if not label:
                    messagebox.showwarning("Required", "Label is required", parent=opt_dialog)
                    return

                description = desc_text.get("1.0", "end-1c").strip()
                emoji = emoji_entry.get().strip()
                value = label.lower().replace(" ", "_")
                is_default = default_var.get()

                options_list.append(SelectOption(
                    label=label,
                    value=value,
                    description=description,
                    emoji=emoji,
                    default=is_default
                ))
                refresh_options()
                opt_dialog.destroy()

            PremiumButton(opt_btn_frame, text="Cancel", width=120, fg_color=PREMIUM_CARD_HOVER,
                         hover_color=PREMIUM_BORDER, command=opt_dialog.destroy).pack(side="left")
            PremiumButton(opt_btn_frame, text="Add", width=120, command=save_option).pack(side="right")

        def edit_option(idx):
            """Edit an existing option."""
            opt = options_list[idx]

            # Create option editor dialog
            opt_dialog = ctk.CTkToplevel(dialog)
            opt_dialog.title("Edit Option")
            opt_dialog.geometry("500x440")
            opt_dialog.grab_set()

            # Center
            opt_dialog.update_idletasks()
            ox = dialog.winfo_x() + (dialog.winfo_width() // 2) - 250
            oy = dialog.winfo_y() + (dialog.winfo_height() // 2) - 220
            opt_dialog.geometry(f"+{ox}+{oy}")

            opt_content = ctk.CTkFrame(opt_dialog, fg_color="transparent")
            opt_content.pack(fill="both", expand=True, padx=20, pady=20)

            # Label (required)
            ctk.CTkLabel(opt_content, text="Label (Required)", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 5))
            label_entry = PremiumEntry(opt_content, placeholder_text="Option name")
            label_entry.insert(0, opt.label)
            label_entry.pack(fill="x", pady=(0, 15))
            label_entry.focus()

            # Description (optional)
            ctk.CTkLabel(opt_content, text="Description (Optional)", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(5, 5))
            desc_text = PremiumTextbox(opt_content, height=80)
            if opt.description:
                desc_text.insert("1.0", opt.description)
            desc_text.pack(fill="x", pady=(0, 15))

            # Emoji (optional)
            ctk.CTkLabel(opt_content, text="Emoji (Optional)", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(5, 5))
            emoji_entry = PremiumEntry(opt_content, placeholder_text="😀")
            if opt.emoji:
                emoji_entry.insert(0, opt.emoji)
            emoji_entry.pack(fill="x", pady=(0, 15))

            # Default checkbox
            default_var = tk.BooleanVar(value=opt.default)
            ctk.CTkCheckBox(
                opt_content,
                text="⭐ Mark as Default (Pre-selected option)",
                variable=default_var,
                font=("Segoe UI", 11)
            ).pack(anchor="w", pady=(5, 20))

            # Buttons
            opt_btn_frame = ctk.CTkFrame(opt_content, fg_color="transparent")
            opt_btn_frame.pack(fill="x")

            def save_changes():
                label = label_entry.get().strip()
                if not label:
                    messagebox.showwarning("Required", "Label is required", parent=opt_dialog)
                    return

                description = desc_text.get("1.0", "end-1c").strip()
                emoji = emoji_entry.get().strip()
                value = label.lower().replace(" ", "_")
                is_default = default_var.get()

                options_list[idx] = SelectOption(
                    label=label,
                    value=value,
                    description=description,
                    emoji=emoji,
                    default=is_default
                )
                refresh_options()
                opt_dialog.destroy()

            PremiumButton(opt_btn_frame, text="Cancel", width=120, fg_color=PREMIUM_CARD_HOVER,
                         hover_color=PREMIUM_BORDER, command=opt_dialog.destroy).pack(side="left")
            PremiumButton(opt_btn_frame, text="Save", width=120, command=save_changes).pack(side="right")

        def refresh_options():
            for widget in options_frame.winfo_children():
                widget.destroy()

            for i, opt in enumerate(options_list):
                frame = ctk.CTkFrame(options_frame, fg_color=PREMIUM_CARD, corner_radius=8)
                frame.pack(fill="x", pady=3, padx=5)

                # Info
                info_frame = ctk.CTkFrame(frame, fg_color="transparent")
                info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=8)

                # Label with emoji and default indicator
                label_text = f"{opt.emoji} {opt.label}" if opt.emoji else opt.label
                if opt.default:
                    label_text = f"⭐ {label_text}"
                ctk.CTkLabel(info_frame, text=label_text, font=("Segoe UI", 11, "bold")).pack(anchor="w")

                # Description if exists
                if opt.description:
                    desc_text = opt.description[:50] + "..." if len(opt.description) > 50 else opt.description
                    ctk.CTkLabel(
                        info_frame,
                        text=desc_text,
                        font=("Segoe UI", 9),
                        text_color=PREMIUM_TEXT_DIM
                    ).pack(anchor="w")

                # Buttons
                btn_container = ctk.CTkFrame(frame, fg_color="transparent")
                btn_container.pack(side="right", padx=5)

                ctk.CTkButton(
                    btn_container,
                    text="✏️",
                    width=30,
                    height=28,
                    fg_color=PREMIUM_ACCENT,
                    command=lambda idx=i: edit_option(idx)
                ).pack(side="left", padx=2)

                ctk.CTkButton(
                    btn_container,
                    text="✕",
                    width=30,
                    height=28,
                    fg_color=PREMIUM_DANGER,
                    command=lambda idx=i: remove_option(idx)
                ).pack(side="left", padx=2)

        def remove_option(idx):
            options_list.pop(idx)
            refresh_options()

        PremiumButton(content, text="+ Add Option", width=140, height=32, command=add_option).pack(pady=(0, 15))

        # Buttons
        btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        btn_frame.pack(fill="x")

        def add():
            placeholder = placeholder_entry.get().strip()

            if not options_list:
                messagebox.showwarning("Required", "Add at least one option", parent=dialog)
                return

            menu = SelectMenu(placeholder=placeholder, options=options_list)
            errors = menu.validate()

            if errors:
                messagebox.showerror("Validation Error", "\n".join(errors), parent=dialog)
                return

            self.select_menus.append(menu)
            self.refresh_menus_list()
            dialog.destroy()

        PremiumButton(btn_frame, text="Cancel", width=120, fg_color=PREMIUM_CARD_HOVER,
                     hover_color=PREMIUM_BORDER, command=dialog.destroy).pack(side="left")
        PremiumButton(btn_frame, text="Add Menu", width=120, command=add).pack(side="right")

    def refresh_buttons_list(self):
        """Refresh buttons list display."""
        for widget in self.buttons_container.winfo_children():
            widget.destroy()

        if not self.buttons:
            ctk.CTkLabel(
                self.buttons_container,
                text="No buttons added yet",
                font=("Segoe UI", 12),
                text_color=PREMIUM_TEXT_DIM
            ).pack(pady=20)
            return

        for i, button in enumerate(self.buttons):
            self.create_button_card(i, button)

    def create_button_card(self, index, button):
        """Create a button display card."""
        card = ctk.CTkFrame(self.buttons_container, fg_color=PREMIUM_CARD, corner_radius=10)
        card.pack(fill="x", pady=5)

        # Style color indicator
        style_colors = {
            "primary": PREMIUM_ACCENT,
            "secondary": "#4e5058",
            "success": PREMIUM_SUCCESS,
            "danger": PREMIUM_DANGER,
            "link": "#00aff4"
        }
        color = style_colors.get(button.style, PREMIUM_ACCENT)

        # Color bar
        color_bar = ctk.CTkFrame(card, fg_color=color, width=6, corner_radius=0)
        color_bar.pack(side="left", fill="y")

        # Info
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=12, pady=10)

        label_text = f"{button.emoji} {button.label}" if button.emoji else button.label
        ctk.CTkLabel(info_frame, text=label_text, font=("Segoe UI", 12, "bold")).pack(anchor="w")

        style_text = f"Style: {button.style.capitalize()}"
        if button.url:
            style_text += f" | URL: {button.url[:40]}..."

        ctk.CTkLabel(info_frame, text=style_text, font=("Segoe UI", 10), text_color=PREMIUM_TEXT_DIM).pack(anchor="w")

        # Delete button
        ctk.CTkButton(
            card,
            text="🗑",
            width=35,
            height=35,
            fg_color=PREMIUM_DANGER,
            hover_color="#c23538",
            command=lambda: self.delete_button(index)
        ).pack(side="right", padx=10)

    def delete_button(self, index):
        """Delete a button."""
        self.buttons.pop(index)
        self.refresh_buttons_list()

    def refresh_menus_list(self):
        """Refresh select menus list display."""
        for widget in self.menus_container.winfo_children():
            widget.destroy()

        if not self.select_menus:
            ctk.CTkLabel(
                self.menus_container,
                text="No select menus added yet",
                font=("Segoe UI", 12),
                text_color=PREMIUM_TEXT_DIM
            ).pack(pady=20)
            return

        for i, menu in enumerate(self.select_menus):
            self.create_menu_card(i, menu)

    def create_menu_card(self, index, menu):
        """Create a select menu display card."""
        card = ctk.CTkFrame(self.menus_container, fg_color=PREMIUM_CARD, corner_radius=10)
        card.pack(fill="x", pady=5)

        # Info
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=12, pady=10)

        ctk.CTkLabel(info_frame, text=menu.placeholder, font=("Segoe UI", 12, "bold")).pack(anchor="w")

        options_text = f"{len(menu.options)} options"
        ctk.CTkLabel(info_frame, text=options_text, font=("Segoe UI", 10), text_color=PREMIUM_TEXT_DIM).pack(anchor="w")

        # Delete button
        ctk.CTkButton(
            card,
            text="🗑",
            width=35,
            height=35,
            fg_color=PREMIUM_DANGER,
            hover_color="#c23538",
            command=lambda: self.delete_menu(index)
        ).pack(side="right", padx=10)

    def delete_menu(self, index):
        """Delete a select menu."""
        self.select_menus.pop(index)
        self.refresh_menus_list()

    # ========================================================================
    # PREVIEW
    # ========================================================================

    def update_preview(self):
        """Update the live preview."""
        # Get current values
        self.sync_embed_from_ui()

        # Clear canvas
        self.preview_canvas.delete("all")

        # Draw embed
        self.draw_embed_preview()

        # Update status bar
        self.update_status_bar()

    def sync_embed_from_ui(self):
        """Sync embed object from UI inputs."""
        self.current_embed.title = self.title_entry.get().strip()
        self.current_embed.description = self.desc_text.get("1.0", "end-1c").strip()
        self.current_embed.url = self.url_entry.get().strip()
        self.current_embed.color = self.color_entry.get().strip() or "#5865F2"
        self.current_embed.author = self.author_entry.get().strip()
        self.current_embed.author_icon = self.author_icon_entry.get().strip()
        self.current_embed.author_url = self.author_url_entry.get().strip()
        self.current_embed.footer = self.footer_entry.get().strip()
        self.current_embed.footer_icon = self.footer_icon_entry.get().strip()
        self.current_embed.thumbnail = self.thumbnail_entry.get().strip()
        self.current_embed.image = self.image_entry.get().strip()
        self.current_embed.timestamp = self.timestamp_var.get()

    def draw_embed_preview(self):
        """Draw the embed on canvas."""
        canvas = self.preview_canvas

        # Theme colors
        theme_colors = {
            "dark": {"bg": "#36393f", "card": "#2f3136", "text": "#ffffff", "text_dim": "#dcddde"},
            "light": {"bg": "#ffffff", "card": "#f2f3f5", "text": "#060607", "text_dim": "#4e5058"},
            "amoled": {"bg": "#000000", "card": "#0a0a0a", "text": "#ffffff", "text_dim": "#b0b0b0"}
        }

        colors = theme_colors.get(self.preview_theme, theme_colors["dark"])
        canvas.configure(bg=colors["bg"])

        # Embed card dimensions
        padding = 10
        card_x = padding
        card_y = padding
        card_width = 400

        # Background
        canvas.create_rectangle(
            card_x, card_y, card_x + card_width, card_y + 600,
            fill=colors["card"],
            outline=""
        )

        # Color bar
        if self.current_embed.color:
            try:
                color = self.current_embed.color
                canvas.create_rectangle(
                    card_x, card_y, card_x + 4, card_y + 600,
                    fill=color,
                    outline=""
                )
            except:
                pass

        # Current Y position
        y = card_y + 16
        x = card_x + 16
        max_width = card_width - 32

        # Thumbnail (top right)
        thumbnail_size = 80
        if self.current_embed.thumbnail:
            thumb_x = card_x + card_width - thumbnail_size - 16
            thumb_y = y
            # Draw placeholder
            canvas.create_rectangle(
                thumb_x, thumb_y,
                thumb_x + thumbnail_size, thumb_y + thumbnail_size,
                fill=colors["bg"],
                outline=colors["text_dim"],
                width=2
            )
            canvas.create_text(
                thumb_x + thumbnail_size // 2, thumb_y + thumbnail_size // 2,
                text="🖼️\nThumbnail",
                font=("Segoe UI", 9),
                fill=colors["text_dim"],
                justify="center"
            )

        # Author with icon
        if self.current_embed.author:
            author_x = x
            # Author icon if exists
            if self.current_embed.author_icon:
                icon_size = 24
                canvas.create_oval(
                    author_x, y,
                    author_x + icon_size, y + icon_size,
                    fill=colors["bg"],
                    outline=colors["text_dim"],
                    width=2
                )
                canvas.create_text(
                    author_x + icon_size // 2, y + icon_size // 2,
                    text="👤",
                    font=("Segoe UI", 10),
                    fill=colors["text_dim"]
                )
                author_x += icon_size + 8

            canvas.create_text(
                author_x, y + 4,
                text=self.current_embed.author,
                font=("Segoe UI", 11, "bold"),
                fill=colors["text"],
                anchor="nw",
                width=max_width - 100
            )
            y += 34

        # Title
        if self.current_embed.title:
            canvas.create_text(
                x, y,
                text=self.current_embed.title,
                font=("Segoe UI", 14, "bold"),
                fill="#00b0f4" if self.current_embed.url else colors["text"],
                anchor="nw",
                width=max_width - 100  # Leave space for thumbnail
            )
            y += 35

        # Description
        if self.current_embed.description:
            desc = self.current_embed.description[:500]
            if len(self.current_embed.description) > 500:
                desc += "..."
            canvas.create_text(
                x, y,
                text=desc,
                font=("Segoe UI", 11),
                fill=colors["text_dim"],
                anchor="nw",
                width=max_width - 100
            )
            # Estimate height
            lines = len(desc) // 60 + 1
            y += lines * 20 + 10

        # Fields
        if self.current_embed.fields:
            y += 10
            inline_count = 0
            inline_x = x

            for field in self.current_embed.fields[:10]:  # Show max 10 in preview
                if field.inline:
                    field_width = (max_width - 20) // 3
                    canvas.create_text(
                        inline_x, y,
                        text=field.name,
                        font=("Segoe UI", 10, "bold"),
                        fill="#ffffff",
                        anchor="nw",
                        width=field_width - 10
                    )
                    canvas.create_text(
                        inline_x, y + 20,
                        text=field.value[:50],
                        font=("Segoe UI", 9),
                        fill="#b9bbbe",
                        anchor="nw",
                        width=field_width - 10
                    )

                    inline_count += 1
                    inline_x += field_width

                    if inline_count >= 3:
                        inline_count = 0
                        inline_x = x
                        y += 70
                else:
                    if inline_count > 0:
                        y += 70
                        inline_count = 0
                        inline_x = x

                    canvas.create_text(
                        x, y,
                        text=field.name,
                        font=("Segoe UI", 10, "bold"),
                        fill="#ffffff",
                        anchor="nw",
                        width=max_width
                    )
                    canvas.create_text(
                        x, y + 20,
                        text=field.value[:100],
                        font=("Segoe UI", 9),
                        fill="#b9bbbe",
                        anchor="nw",
                        width=max_width
                    )
                    y += 70

            if inline_count > 0:
                y += 70

        # Main Image
        if self.current_embed.image:
            y += 10
            image_width = max_width - 20
            image_height = 200
            canvas.create_rectangle(
                x, y,
                x + image_width, y + image_height,
                fill=colors["bg"],
                outline=colors["text_dim"],
                width=2
            )
            canvas.create_text(
                x + image_width // 2, y + image_height // 2,
                text="🖼️\nMain Image\n(Large Preview)",
                font=("Segoe UI", 11),
                fill=colors["text_dim"],
                justify="center"
            )
            y += image_height + 15

        # Footer with icon
        if self.current_embed.footer:
            y = max(y, card_y + 550)
            footer_x = x

            # Footer icon if exists
            if self.current_embed.footer_icon:
                icon_size = 20
                canvas.create_oval(
                    footer_x, y - icon_size,
                    footer_x + icon_size, y,
                    fill=colors["bg"],
                    outline=colors["text_dim"],
                    width=1
                )
                canvas.create_text(
                    footer_x + icon_size // 2, y - icon_size // 2,
                    text="📌",
                    font=("Segoe UI", 8),
                    fill=colors["text_dim"]
                )
                footer_x += icon_size + 6

            canvas.create_text(
                footer_x, y,
                text=self.current_embed.footer,
                font=("Segoe UI", 9),
                fill="#72767d",
                anchor="sw"
            )

    # ========================================================================
    # TEMPLATES & HISTORY
    # ========================================================================

    def show_templates(self):
        """Show templates gallery."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Templates Gallery")
        dialog.geometry("700x600")
        dialog.grab_set()

        # Header
        header = ctk.CTkFrame(dialog, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=15)

        ctk.CTkLabel(
            header,
            text="Templates",
            font=("Segoe UI", 20, "bold")
        ).pack(side="left")

        PremiumButton(
            header,
            text="💾 Save Current",
            width=140,
            command=lambda: self.save_as_template(dialog)
        ).pack(side="right")

        # Templates list
        scroll = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Add default templates if empty
        if not self.templates:
            self.add_default_templates()

        # Show templates
        for i, template in enumerate(self.templates):
            self.create_template_card(scroll, template, i, dialog)

    def create_template_card(self, parent, template, index, dialog):
        """Create a template card."""
        card = ctk.CTkFrame(parent, fg_color=PREMIUM_CARD, corner_radius=12)
        card.pack(fill="x", pady=5)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="x", padx=15, pady=12)

        # Info
        info = ctk.CTkFrame(content, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            info,
            text=template.get("name", "Untitled"),
            font=("Segoe UI", 14, "bold"),
            anchor="w"
        ).pack(anchor="w")

        ctk.CTkLabel(
            info,
            text=template.get("description", "No description"),
            font=("Segoe UI", 10),
            text_color=PREMIUM_TEXT_DIM,
            anchor="w"
        ).pack(anchor="w", pady=(2, 0))

        # Actions
        actions = ctk.CTkFrame(content, fg_color="transparent")
        actions.pack(side="right")

        PremiumButton(
            actions,
            text="Use",
            width=80,
            height=32,
            command=lambda: self.load_template(template, dialog)
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            actions,
            text="🗑️",
            width=40,
            height=32,
            fg_color="transparent",
            hover_color=PREMIUM_DANGER,
            command=lambda: self.delete_template(index, dialog)
        ).pack(side="left")

    def add_default_templates(self): # add better formats later {reminder optional}
        """Add default templates.""" 
        self.templates = [
            {
                "name": "Announcement",
                "description": "Server announcement template",
                "embed": {
                    "title": "📢 Server Announcement",
                    "description": "Important announcement goes here...",
                    "color": "#5865F2",
                    "footer": "Posted by Admin Team",
                    "timestamp": True,
                    "fields": []
                }
            },
            {
                "name": "Welcome Message",
                "description": "Welcome new members",
                "embed": {
                    "title": "👋 Welcome!",
                    "description": "Welcome to our server! We're glad to have you here.",
                    "color": "#3BA55C",
                    "fields": [
                        {"name": "📜 Rules", "value": "Check out #rules", "inline": True},
                        {"name": "💬 Chat", "value": "Join us in #general", "inline": True},
                        {"name": "❓ Help", "value": "Ask in #support", "inline": True}
                    ]
                }
            },
            {
                "name": "Server Status",
                "description": "Display server statistics",
                "embed": {
                    "title": "📊 Server Status",
                    "color": "#FAA61A",
                    "fields": [
                        {"name": "Status", "value": "🟢 Online", "inline": True},
                        {"name": "Players", "value": "42/100", "inline": True},
                        {"name": "Uptime", "value": "7 days", "inline": True}
                    ],
                    "footer": "Last updated",
                    "timestamp": True
                }
            }
        ]
        self.save_templates()

    def save_as_template(self, dialog):
        """Save current embed as template."""
        name = ctk.CTkInputDialog(
            text="Template Name:",
            title="Save Template"
        ).get_input()

        if not name:
            return

        desc = ctk.CTkInputDialog(
            text="Description (optional):",
            title="Template Description"
        ).get_input()

        self.sync_embed_from_ui()

        template = {
            "name": name,
            "description": desc or "",
            "embed": asdict(self.current_embed)
        }

        self.templates.append(template)
        self.save_templates()

        messagebox.showinfo("Saved", "Template saved successfully!")
        dialog.destroy()
        self.show_templates()

    def load_template(self, template, dialog):
        """Load a template."""
        try:
            embed_data = template["embed"]

            # Rebuild Embed object
            fields = [EmbedField(**f) for f in embed_data.get("fields", [])]
            embed_data["fields"] = fields

            self.current_embed = Embed(**embed_data)
            self.load_embed_to_ui()
            self.update_preview()

            dialog.destroy()
            messagebox.showinfo("Loaded", f"Template '{template['name']}' loaded!")
        except Exception as e:
            logger.error(f"Failed to load template: {e}")
            messagebox.showerror("Error", "Failed to load template")

    def delete_template(self, index, dialog):
        """Delete a template."""
        if messagebox.askyesno("Confirm", "Delete this template?"):
            del self.templates[index]
            self.save_templates()
            dialog.destroy()
            self.show_templates()

    def load_embed_to_ui(self):
        """Load embed data to UI fields."""
        self.title_entry.delete(0, "end")
        self.title_entry.insert(0, self.current_embed.title)

        self.desc_text.delete("1.0", "end")
        self.desc_text.insert("1.0", self.current_embed.description)

        self.url_entry.delete(0, "end")
        self.url_entry.insert(0, self.current_embed.url)

        self.color_entry.delete(0, "end")
        self.color_entry.insert(0, self.current_embed.color)
        self.color_picker.update_color(self.current_embed.color)

        self.author_entry.delete(0, "end")
        self.author_entry.insert(0, self.current_embed.author)

        self.author_icon_entry.delete(0, "end")
        self.author_icon_entry.insert(0, self.current_embed.author_icon)

        self.author_url_entry.delete(0, "end")
        self.author_url_entry.insert(0, self.current_embed.author_url)

        self.footer_entry.delete(0, "end")
        self.footer_entry.insert(0, self.current_embed.footer)

        self.footer_icon_entry.delete(0, "end")
        self.footer_icon_entry.insert(0, self.current_embed.footer_icon)

        self.thumbnail_entry.delete(0, "end")
        self.thumbnail_entry.insert(0, self.current_embed.thumbnail)

        self.image_entry.delete(0, "end")
        self.image_entry.insert(0, self.current_embed.image)

        self.timestamp_var.set(self.current_embed.timestamp)

        self.refresh_fields_list()

    def show_history(self):
        """Show embed history."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("History")
        dialog.geometry("700x600")
        dialog.grab_set()

        # Header
        header = ctk.CTkFrame(dialog, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=15)

        ctk.CTkLabel(
            header,
            text="Recent Embeds",
            font=("Segoe UI", 20, "bold")
        ).pack(side="left")

        PremiumButton(
            header,
            text="Clear All",
            width=120,
            fg_color=PREMIUM_DANGER,
            command=lambda: self.clear_history(dialog)
        ).pack(side="right")

        # History list
        scroll = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        if not self.history:
            ctk.CTkLabel(
                scroll,
                text="No history yet",
                font=("Segoe UI", 13),
                text_color=PREMIUM_TEXT_DIM
            ).pack(pady=50)
        else:
            for i, embed in enumerate(reversed(self.history[-20:])):  # Show last 20
                self.create_history_card(scroll, embed, i, dialog)

    def create_history_card(self, parent, embed, index, dialog):
        """Create a history card."""
        card = ctk.CTkFrame(parent, fg_color=PREMIUM_CARD, corner_radius=12)
        card.pack(fill="x", pady=5)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="x", padx=15, pady=12)

        # Info
        info = ctk.CTkFrame(content, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True)

        title = embed.title or "Untitled Embed"
        ctk.CTkLabel(
            info,
            text=title,
            font=("Segoe UI", 13, "bold"),
            anchor="w"
        ).pack(anchor="w")

        desc_preview = (embed.description[:60] + "...") if len(embed.description) > 60 else embed.description
        if desc_preview:
            ctk.CTkLabel(
                info,
                text=desc_preview,
                font=("Segoe UI", 10),
                text_color=PREMIUM_TEXT_DIM,
                anchor="w"
            ).pack(anchor="w", pady=(2, 0))

        # Actions
        PremiumButton(
            content,
            text="Restore",
            width=100,
            height=32,
            command=lambda: self.restore_from_history(embed, dialog)
        ).pack(side="right")

    def restore_from_history(self, embed, dialog):
        """Restore embed from history."""
        self.current_embed = embed
        self.load_embed_to_ui()
        self.update_preview()
        dialog.destroy()
        messagebox.showinfo("Restored", "Embed restored from history!")

    def clear_history(self, dialog):
        """Clear all history."""
        if messagebox.askyesno("Confirm", "Clear all history?"):
            self.history = []
            self.save_history()
            dialog.destroy()
            messagebox.showinfo("Cleared", "History cleared!")

    # ========================================================================
    # EXPORT & SEND
    # ========================================================================

    def show_export_menu(self):
        """Show export options menu."""
        menu = ctk.CTkToplevel(self)
        menu.title("Export Options")
        menu.geometry("400x300")
        menu.grab_set()

        # Center
        menu.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (menu.winfo_width() // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (menu.winfo_height() // 2)
        menu.geometry(f"+{x}+{y}")

        ctk.CTkLabel(
            menu,
            text="Export As",
            font=("Segoe UI", 20, "bold")
        ).pack(pady=20)

        export_options = [
            ("📄 JSON File", self.export_json),
            ("🐍 Python Code", self.export_python), # fix this issue {reminder imp}
            ("📗 Node.js Code", self.export_nodejs),
            ("📋 Copy JSON", self.copy_json),
        ]

        for text, command in export_options:
            PremiumButton(
                menu,
                text=text,
                height=45,
                font=("Segoe UI", 14),
                command=lambda cmd=command: (cmd(), menu.destroy())
            ).pack(fill="x", padx=40, pady=5)

    def export_json(self):
        """Export as JSON file."""
        self.sync_embed_from_ui()

        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )

        if file_path:
            payload = {"embeds": [self.current_embed.to_dict()]}

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)

            messagebox.showinfo("Exported", f"Exported to:\n{file_path}")

    def export_python(self):
        """Export as Python code."""
        self.sync_embed_from_ui()

        file_path = filedialog.asksaveasfilename(
            defaultextension=".py",
            filetypes=[("Python Files", "*.py"), ("All Files", "*.*")]
        )

        if file_path:
            embed_dict = self.current_embed.to_dict()
            code = f"""import requests

webhook_url = "YOUR_WEBHOOK_URL_HERE"

embed = {json.dumps(embed_dict, indent=4)}

payload = {{"embeds": [embed]}}

response = requests.post(webhook_url, json=payload)
print(f"Status: {{response.status_code}}")
"""

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(code)

            messagebox.showinfo("Exported", f"Python code exported to:\n{file_path}")

    def export_nodejs(self):
        """Export as Node.js code."""
        self.sync_embed_from_ui()

        file_path = filedialog.asksaveasfilename(
            defaultextension=".js",
            filetypes=[("JavaScript Files", "*.js"), ("All Files", "*.*")]
        )

        if file_path:
            embed_dict = self.current_embed.to_dict()
            code = f"""const axios = require('axios');

const webhookURL = 'YOUR_WEBHOOK_URL_HERE';

const embed = {json.dumps(embed_dict, indent=2)};

const payload = {{ embeds: [embed] }};

axios.post(webhookURL, payload)
  .then(response => console.log('Sent!'))
  .catch(error => console.error('Error:', error));
"""

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(code)

            messagebox.showinfo("Exported", f"Node.js code exported to:\n{file_path}")

    def copy_json(self):
        """Copy JSON to clipboard."""
        self.sync_embed_from_ui()

        payload = {"embeds": [self.current_embed.to_dict()]}
        json_str = json.dumps(payload, indent=2, ensure_ascii=False)

        self.clipboard_clear()
        self.clipboard_append(json_str)

        messagebox.showinfo("Copied", "JSON copied to clipboard!")

    def send_webhook(self):
        """Send webhook to Discord with optional profile customization."""
        self.sync_embed_from_ui()

        # Validate first
        errors = self.current_embed.validate()
        if errors:
            result = messagebox.askyesnocancel(
                "Validation Errors",
                f"Found errors:\n\n" + "\n".join(errors[:5]) + "\n\nSend anyway?"
            )
            if not result:
                return

        # Create webhook send dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title("Send Webhook")
        dialog.geometry("550x480")
        dialog.grab_set()

        # Center dialog
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        # Content
        content = ctk.CTkFrame(dialog, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=20)

        # Webhook URL (Required)
        ctk.CTkLabel(content, text="Webhook URL", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 5))
        ctk.CTkLabel(content, text="Required - Get this from Discord channel settings",
                    font=("Segoe UI", 10), text_color=PREMIUM_TEXT_DIM).pack(anchor="w", pady=(0, 5))
        url_entry = PremiumEntry(content, placeholder_text="https://discord.com/api/webhooks/...")
        url_entry.pack(fill="x", pady=(0, 15))
        # Pre-fill from saved settings
        if self.webhook_settings.get("url"):
            url_entry.insert(0, self.webhook_settings["url"])

        # Webhook Username (Optional)
        ctk.CTkLabel(content, text="Bot Username (Optional)", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(5, 5))
        ctk.CTkLabel(content, text="Custom name to display instead of default webhook name",
                    font=("Segoe UI", 10), text_color=PREMIUM_TEXT_DIM).pack(anchor="w", pady=(0, 5))
        username_entry = PremiumEntry(content, placeholder_text="Cool Bot")
        username_entry.pack(fill="x", pady=(0, 15))
        # Pre-fill from saved settings
        if self.webhook_settings.get("username"):
            username_entry.insert(0, self.webhook_settings["username"])

        # Avatar URL (Optional)
        ctk.CTkLabel(content, text="Bot Avatar URL (Optional)", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(5, 5))
        ctk.CTkLabel(content, text="Image URL to use as bot profile picture",
                    font=("Segoe UI", 10), text_color=PREMIUM_TEXT_DIM).pack(anchor="w", pady=(0, 5))
        avatar_entry = PremiumEntry(content, placeholder_text="https://example.com/avatar.png")
        avatar_entry.pack(fill="x", pady=(0, 15))
        # Pre-fill from saved settings
        if self.webhook_settings.get("avatar_url"):
            avatar_entry.insert(0, self.webhook_settings["avatar_url"])

        # Remember settings checkbox
        remember_var = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            content,
            text="💾 Remember these settings for next time",
            variable=remember_var,
            font=("Segoe UI", 11)
        ).pack(anchor="w", pady=(5, 20))

        # Result variables - store values before dialog is destroyed
        send_clicked = tk.BooleanVar(value=False)
        result_data = {}

        # Buttons
        btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        btn_frame.pack(fill="x")

        def send():
            url = url_entry.get().strip()

            if not url:
                messagebox.showwarning("Required", "Webhook URL is required", parent=dialog)
                return

            # Validate URL
            if "discord.com/api/webhooks/" not in url and "discordapp.com/api/webhooks/" not in url:
                messagebox.showerror("Invalid URL", "Please enter a valid Discord webhook URL", parent=dialog)
                return

            # Validate avatar URL if provided
            avatar_url = avatar_entry.get().strip()
            if avatar_url and not avatar_url.startswith(("http://", "https://")):
                messagebox.showerror("Invalid URL", "Avatar URL must start with http:// or https://", parent=dialog)
                return

            # Store values BEFORE destroying dialog
            result_data['url'] = url
            result_data['username'] = username_entry.get().strip()
            result_data['avatar_url'] = avatar_url
            result_data['remember'] = remember_var.get()

            send_clicked.set(True)
            dialog.destroy()

        PremiumButton(btn_frame, text="Cancel", width=120, fg_color=PREMIUM_CARD_HOVER,
                     hover_color=PREMIUM_BORDER, command=dialog.destroy).pack(side="left")
        PremiumButton(btn_frame, text="🚀 Send", width=120, command=send).pack(side="right")

        # Wait for dialog
        self.wait_window(dialog)

        # If cancelled, return
        if not send_clicked.get():
            return

        # Get values from stored data
        url = result_data.get('url', '')
        username = result_data.get('username', '')
        avatar_url = result_data.get('avatar_url', '')
        remember = result_data.get('remember', False)

        # Save settings if remember is checked
        if remember:
            self.webhook_settings = {
                "url": url,
                "username": username,
                "avatar_url": avatar_url
            }
            self.save_webhook_settings()

        # Build payload
        payload = {"embeds": [self.current_embed.to_dict()]}

        # Add optional fields
        if username:
            payload["username"] = username
        if avatar_url:
            payload["avatar_url"] = avatar_url

        # Debug: Show payload option
        import json
        show_debug = messagebox.askyesno(
            "Debug Mode",
            "Do you want to see the payload before sending?\n(Useful for debugging)",
            default=messagebox.NO
        )

        if show_debug:
            payload_str = json.dumps(payload, indent=2)
            debug_dialog = ctk.CTkToplevel(self)
            debug_dialog.title("Payload Debug")
            debug_dialog.geometry("700x600")
            debug_dialog.grab_set()

            text_box = ctk.CTkTextbox(debug_dialog, font=("Consolas", 10))
            text_box.pack(fill="both", expand=True, padx=20, pady=20)
            text_box.insert("1.0", payload_str)
            text_box.configure(state="disabled")

            ctk.CTkButton(
                debug_dialog,
                text="Copy to Clipboard",
                command=lambda: self.clipboard_append(payload_str)
            ).pack(pady=(0, 20))

        # Send
        try:
            response = requests.post(url, json=payload, timeout=10)

            if response.status_code in (200, 204):
                messagebox.showinfo("Success", "✅ Embed sent successfully!\n\nCheck your Discord channel.")

                # Add to history
                import copy
                self.history.append(copy.deepcopy(self.current_embed))
                self.save_history()
            else:
                # Enhanced error message
                error_msg = f"❌ Discord returned an error:\n\n"
                error_msg += f"Status Code: {response.status_code}\n\n"

                try:
                    error_json = response.json()
                    error_msg += f"Error: {error_json.get('message', 'Unknown error')}\n\n"
                    if 'errors' in error_json:
                        error_msg += f"Details:\n{json.dumps(error_json['errors'], indent=2)}"
                except:
                    error_msg += f"Response: {response.text[:300]}"

                messagebox.showerror("Discord Error", error_msg)

        except Exception as e:
            messagebox.showerror("Network Error", f"❌ Failed to send webhook:\n\n{str(e)}\n\nCheck your internet connection and webhook URL.")

    # ========================================================================
    # AUTO-SAVE & PERSISTENCE
    # ========================================================================

    def start_auto_save(self):
        """Start auto-save timer."""
        self.auto_save()
        self.auto_save_id = self.after(AUTO_SAVE_INTERVAL, self.start_auto_save)

    def auto_save(self):
        """Auto-save current embed."""
        try:
            self.sync_embed_from_ui()
            # Save is implicit - handled by history
        except Exception as e:
            logger.error(f"Auto-save failed: {e}")

    def save_history(self):
        """Save history to file."""
        try:
            data = [asdict(e) for e in self.history[-50:]]  # Keep last 50
            with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save history: {e}")

    def load_history(self):
        """Load history from file."""
        try:
            if os.path.exists(HISTORY_FILE):
                with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                self.history = []
                for item in data:
                    fields = [EmbedField(**f) for f in item.get("fields", [])]
                    item["fields"] = fields
                    self.history.append(Embed(**item))
        except Exception as e:
            logger.error(f"Failed to load history: {e}")
            self.history = []

    def save_templates(self):
        """Save templates to file."""
        try:
            with open(TEMPLATES_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.templates, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save templates: {e}")

    def load_templates(self):
        """Load templates from file."""
        try:
            if os.path.exists(TEMPLATES_FILE):
                with open(TEMPLATES_FILE, 'r', encoding='utf-8') as f:
                    self.templates = json.load(f)
            else:
                self.templates = []
        except Exception as e:
            logger.error(f"Failed to load templates: {e}")
            self.templates = []

    def save_webhook_settings(self):
        """Save webhook settings to file."""
        try:
            with open(WEBHOOK_SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.webhook_settings, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save webhook settings: {e}")

    def load_webhook_settings(self):
        """Load webhook settings from file."""
        try:
            if os.path.exists(WEBHOOK_SETTINGS_FILE):
                with open(WEBHOOK_SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    self.webhook_settings = json.load(f)
            else:
                self.webhook_settings = {"url": "", "username": "", "avatar_url": ""}
        except Exception as e:
            logger.error(f"Failed to load webhook settings: {e}")
            self.webhook_settings = {"url": "", "username": "", "avatar_url": ""}

    # ========================================================================
    # KEYBOARD SHORTCUTS
    # ========================================================================

    def bind_shortcuts(self):
        """Bind keyboard shortcuts."""
        self.bind("<Control-s>", lambda e: self.save_as_template(None))
        self.bind("<Control-e>", lambda e: self.show_export_menu())
        self.bind("<Control-Return>", lambda e: self.send_webhook())
        self.bind("<F5>", lambda e: self.update_preview())

    def on_closing(self):
        """Handle window close."""
        if self.auto_save_id:
            self.after_cancel(self.auto_save_id)
        self.destroy()


# ============================================================================
# ENTRY POINT
# ============================================================================

def main():
    """Run the application."""
    app = PremiumEmbedDesigner()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()


if __name__ == "__main__":
    main()
