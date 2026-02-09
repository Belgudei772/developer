from google import genai
from google.genai import types
from rich.markdown import Markdown
from rich.console import Console
from platformdirs import user_config_dir
import json
from pathlib import Path
from tools import read_file, write_file, run_command, list_files

CONFIG_DIR = Path(user_config_dir("myapp"))
CONFIG_FILE = CONFIG_DIR / "config.json"

def load_config():
      if CONFIG_FILE.exists():
          return json.loads(CONFIG_FILE.read_text())
      return {}

def save_config(config):
      CONFIG_DIR.mkdir(parents=True, exist_ok=True)
      CONFIG_FILE.write_text(json.dumps(config, indent=2))

def get_api_key():
      config = load_config()

      if config.get("api_key"):
          return config["api_key"]

      # First time — ask the user
      print("Welcome! Let's set up your API key.")
      print("Get one at: https://aistudio.google.com/apikey\n")
      key = input("Enter your Gemini API key: ").strip()

      config["api_key"] = key
      save_config(config)
      print("Saved! You won't be asked again.\n")

      return key

def main():
    api_key = get_api_key()

    # 1. Create the Gemini client
    client = genai.Client(api_key=api_key)

    # 2. Start a chat session (this keeps conversation history for you)
    chat = client.chats.create(
          model="gemini-2.0-flash",
          config={
              "system_instruction": "You are a coding assistant. Help the user write, debug, and understand code. Keep responses concise.",
              "tools": [read_file, write_file, run_command, list_files],
          }

      )

    console = Console()
    console.print("[bold green]Welcome to MyApp![/bold green]")
    console.print("Type [bold]/quit[/bold] to exit, [bold]/key[/bold] to change API key.\n")

    available_tools = {
    "read_file": read_file,
    "write_file": write_file,
    "run_command": run_command,
    "list_files": list_files,
}

    # 3. The main loop
    while True:
          try:
              user_input = input("> ").strip()
          except (KeyboardInterrupt, EOFError):
              print("\nGoodbye!")
              break

          # Skip empty input
          if not user_input:
              continue

          # Handle commands
          if user_input == "/quit":
              print("Goodbye!")
              break

          if user_input == "/key":
              new_key = input("Enter new API key: ").strip()
              config = load_config()
              config["api_key"] = new_key
              save_config(config)
              console.print("[green]API key updated![/green]")
              continue

          # 4. Send to Gemini and print response
          try:
              response = chat.send_message(user_input)
              while response.function_calls:
                  func_call = response.function_calls[0]
                  tool_name = func_call.name
                  tool_args = func_call.args

                  if tool_name in available_tools:
                      tool_func = available_tools[tool_name]
                      result = tool_func(**tool_args)
                      response = chat.send_message(types.FunctionResponse(name=tool_name, response={"result": result}))
                  else:
                       response = chat.send_message(types.FunctionResponse(name=tool_name, response={"result": f"Error: Unknown tool '{tool_name}'"}))
              console.print(Markdown(response.text))
          except Exception as e:
              console.print(f"[red]Error: {e}[/red]")

if __name__ == "__main__":
    main()