# Developer

> An AI coding assistant that lives in your terminal.

`developer` is a command-line tool that gives you a powerful AI coding assistant, powered by Google's Gemini models. It features a modern, rich terminal interface with streaming responses, syntax highlighting, and keyboard shortcuts.

## Features

- **🎨 Modern TUI**: Beautiful terminal interface built with [Textual](https://textual.textualize.io/)
- **⚡ Streaming Responses**: See the AI response appear in real-time, token by token
- **📜 Chat History**: Navigate through previous messages with ↑/↓ arrows
- **💻 Code Highlighting**: Automatic syntax highlighting for code blocks
- **🔧 Tool Integration**: Read/write files and run shell commands with AI assistance
- **🎯 Keyboard Shortcuts**: Efficient navigation with customizable keybindings
- **📊 Status Bar**: Always-visible model info and connection status

## Installation

### Quick Install

Run the installation script:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Belgudei772/developer/main/install.sh)"
```

This will download the latest release, place it in `~/.local/bin`, and make it executable. If `~/.local/bin` is not in your `PATH`, the script will prompt you to add it.

### Build from Source

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Belgudei772/developer.git
   cd developer
   ```

2. **Create a virtual environment and install dependencies**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python3 src/main.py
   ```

## Usage

1. **Run the application**:
   ```bash
   developer
   ```

2. **Set up your API Key**: The first time you run the tool, it will prompt you to enter your Google Gemini API key. You can get one from [Google AI Studio](https://aistudio.google.com/apikey).

3. **Start Chatting**: Once your key is saved, you can start asking your AI assistant for help.

## Commands

Type `/` followed by a command in the chat:

| Command | Description |
|---------|-------------|
| `/quit` or `/q` | Exit the application |
| `/model` | View or switch to a different Gemini model |
| `/key <api-key>` | Update your Gemini API key |
| `/clear` | Clear the chat history |
| `/help` | Show available commands |

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Enter` | Send message |
| `↑` / `↓` | Navigate command history |
| `Ctrl+C` | Quit application |
| `Ctrl+L` | Clear chat history |
| `Ctrl+M` | Focus input field |
| `Esc` | Blur input field |

## Available Models

- `gemini-2.5-flash` - Fast, efficient model
- `gemini-2.5-pro` - Advanced capabilities
- `gemini-3-flash-preview` - Latest fast model (preview)
- `gemini-3-pro-preview` - Latest advanced model (preview)

## Building

To build a standalone executable:

```bash
pip install pyinstaller
pyinstaller developer.spec
```

The executable will be created in the `dist/` directory.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
