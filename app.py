import os

import tiktoken
from chatlas import ChatBedrockAnthropic
from faicons import icon_svg
from shiny import reactive, render
from shiny.express import input, ui
from shinyswatch import theme


# Function to count tokens
def count_tokens(text):
    """Count the approximate number of tokens in the text using tiktoken."""
    try:
        # Use cl100k_base encoding (used by Claude models)
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except Exception:
        # Fallback to a simple approximation if tiktoken fails
        return len(text.split()) * 1.3  # rough approximation


# Get the directory containing this script
script_dir = os.path.dirname(os.path.abspath(__file__))
# Read from prompt.md file relative to the script
with open(os.path.join(script_dir, "prompt.md"), "r") as f:
    system_prompt = f.read()


# Set some Shiny page options
ui.page_opts(
    # title="Need help? I'm your AI assistant, and I'm here to lend a hand! 🤖",
    title="Ask me anything about gaming! 🤖",
    fillable=True,
    fillable_mobile=True,
    theme=theme.darkly,
)

with ui.layout_sidebar():
    with ui.sidebar(id="prompt_sidebar", open="closed", border=True, width="500px"):
        ui.h5(
            "✨ Tweak the existing system prompt to change the bot's behavior ✨",
            style="text-align: center; color: #00bc8c; text-shadow: 1px 1px 3px rgba(0,0,0,0.3); padding: 10px; border-bottom: 1px solid #444; margin-bottom: 15px; font-weight: 600; letter-spacing: 0.5px;",
        )
        ui.input_text_area(
            "prompt",
            label="Current System Prompt",
            value=system_prompt,
            rows="20",
            cols="10",
            placeholder="Enter your system prompt here",
        )

        # Add a reactive value for token count
        @reactive.calc
        def system_prompt_tokens():
            return count_tokens(input.prompt())

        @render.text
        def token_count():
            tokens = system_prompt_tokens()
            if tokens > 8000:
                return (
                    f"🚨 Warning: System prompt tokens: ~{int(tokens)} "
                    f"(approximate). Crossed 8000 tokens!"
                )
            else:
                return f"System prompt tokens: ~{int(tokens)} (approximate)."

        with ui.tooltip(placement="auto", id="save_tooltip"):
            ui.input_action_button(
                "save_prompt",
                "Apply Changes",
                icon=icon_svg("floppy-disk"),
                class_="btn-success",
            )
            "Save the system prompt to reflect bot's behavior"

    # Create a reactive value for the system prompt
    @reactive.calc
    def current_system_prompt():
        # Start with the initial system prompt
        prompt = system_prompt
        # When the button is clicked, update to the user-provided prompt
        if input.save_prompt() > 0 and input.prompt().strip():
            prompt = input.prompt().strip()
        return prompt

    # Set the system prompt for the chat model reactively
    @reactive.calc
    def get_chat_model():
        return ChatBedrockAnthropic(
            model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
            system_prompt=current_system_prompt(),
        )

    # Create and display chat
    chat = ui.Chat(id="chat")
    chat.ui(
        messages=[
            "What do you want foo?"
        ]
    )


# Define a callback to run when the user submits a message
@chat.on_user_submit
async def handle_user_input(user_input: str):
    # Get the current chat model with the updated system prompt
    response = await get_chat_model().stream_async(user_input)
    await chat.append_message_stream(response)