# Discord Embed Designer

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python)](https://www.python.org/) [![CustomTkinter](https://img.shields.io/badge/CustomTkinter-5.2%2B-purple?style=for-the-badge)](https://github.com/TomSchimansky/CustomTkinter) [![Platform](https://img.shields.io/badge/Platform-Windows-green?style=for-the-badge&logo=windows)](https://www.microsoft.com/windows)

**A modern, feature-rich Discord webhook embed designer with an intuitive GUI**

[Features](#features) • [Installation](#installation) • [Usage](#usage) • [Troubleshooting](#troubleshooting)

</div>

---

## Features

<table>
<tr>
<td>

**Rich Embed Editing**
- Title, Description, URL
- Color customization with picker
- Author with icon and URL
- Footer with icon
- Thumbnail and main images
- Up to 25 custom fields
- Markdown support

</td>
<td>

**User Interface**
- Modern dark theme
- Live preview
- Drag-and-drop field reordering
- Character counters
- Color history
- Inline field formatting

</td>
</tr>
<tr>
<td>

**Data Management**
- Save/load templates
- Embed history
- Auto-save functionality
- Webhook settings persistence
- Export to JSON/Python

</td>
<td>

**Additional Tools**
- URL validation
- Emoji picker
- Markdown toolbar
- Real-time preview
- Multiple theme options
- Standalone EXE support

</td>
</tr>
</table>

---

## Installation

### Option 1: Download Standalone EXE (Recommended)

1. Go to [Releases](https://github.com/yourusername/discord-embed-designer/releases)
2. Download `Discord_Embed_Designer.exe`
3. Run the EXE - no installation needed

> **Note:** Windows Defender may show a warning for unsigned executables. Click "More info" → "Run anyway"

### Option 2: Run from Source

**Requirements:**
- Python 3.8 or higher
- pip (Python package manager)

**Setup:**

```bash
# Clone the repository
git clone https://github.com/yourusername/discord-embed-designer.git
cd discord-embed-designer

# Install dependencies
pip install -r requirements.txt

# Run the application
python discord_webhook.py
```

---

## Usage

### Quick Start

1. **Launch** the application (EXE or Python script)
2. **Create** your embed using the tabs:
   - **Basic:** Title, description, and content
   - **Style:** Colors, author, footer, images
   - **Fields:** Add custom embed fields
3. **Preview** your embed in real-time on the right panel
4. **Send** to your Discord webhook or **Export** as JSON/Python code

### Sending to Discord

1. Click the **Send** button in the top-right
2. Paste your Discord webhook URL
3. Optionally customize bot name and avatar
4. Click **Send**

**Getting a webhook URL:**
```
Discord Server → Channel Settings → Integrations →
Webhooks → New Webhook → Copy Webhook URL
```

### Saving Templates

- Click **Templates** → **Save Current** to save your embed
- Click **Load** to reuse saved templates
- Templates are stored in `templates.json`

---

## Project Structure

```
discord-embed-designer/
├── discord_webhook.py             # Main application
├── requirements.txt               # Python dependencies
├── Discord_Embed_Designer.exe     # Standalone executable
├── templates.json                 # Saved templates (auto-generated)
├── embed_history.json             # Embed history (auto-generated)
└── webhook_settings.json          # Webhook settings (auto-generated)
```

---

## Requirements

### Dependencies

```
customtkinter >= 5.2.0
Pillow >= 10.0.0
requests >= 2.31.0
```

Install all dependencies:
```bash
pip install -r requirements.txt
```

---

## Troubleshooting

### Common Issues

<details>
<summary><b>Discord returns 404 error</b></summary>

**Causes:**
- Invalid webhook URL
- Webhook was deleted
- Invalid URL in embed fields

**Solution:**
1. Verify webhook exists in Discord server settings
2. Copy a fresh webhook URL
3. Ensure all URLs (title, images, etc.) start with `http://` or `https://`
</details>

<details>
<summary><b>Module not found errors (Python)</b></summary>

**Solution:**
```bash
pip install --upgrade customtkinter Pillow requests
```
</details>

<details>
<summary><b>Windows Defender blocks EXE</b></summary>

**Normal behavior for unsigned executables**

**Solution:**
1. Click "More info"
2. Click "Run anyway"

Or add an exclusion in Windows Security settings.
</details>

<details>
<summary><b>Python version error</b></summary>

**Solution:**
- Ensure Python 3.8 or higher is installed
- Check version: `python --version`
- Download latest Python from [python.org](https://www.python.org/downloads/)
</details>

---

## Features Explained

### URL Validation

All URLs are automatically validated:
- Only valid URLs (starting with `http://` or `https://`) are sent
- Invalid URLs are silently ignored
- Prevents Discord API errors

### Character Limits

Discord API limits are enforced:
- **Title:** 256 characters
- **Description:** 4096 characters
- **Fields:** 25 maximum
- **Field name:** 256 characters
- **Field value:** 1024 characters
- **Footer:** 2048 characters
- **Author:** 256 characters

### Markdown Support

Use Discord markdown in description and fields:
```
**bold** *italic* __underline__ ~~strikethrough~~
`code` ```code block```
[link text](https://example.com)
```
---

## Advanced

### Building Your Own EXE

If you want to build your own executable:

```bash
# Install PyInstaller
pip install pyinstaller

# Build
pyinstaller --noconfirm --onefile --windowed \
  --name "Discord_Embed_Designer" \
  discord_webhook.py
```

The EXE will be created in the `dist/` folder.

---

## Built With

- [Python](https://www.python.org/)
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
- [Pillow](https://python-pillow.org/)
- [Requests](https://requests.readthedocs.io/)

---

## Developer

<div align="center">

**Created by oniisama**

[![Discord](https://img.shields.io/badge/Discord-oniisama-5865F2?style=for-the-badge&logo=discord&logoColor=white)](https://discord.com/users/758650374500122644)

*Click the badge to contact me on Discord!*

</div>
