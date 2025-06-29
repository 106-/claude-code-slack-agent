import os
import logging
import traceback
import yaml
import json
import argparse
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from claude_code_sdk import (
    query,
    ClaudeCodeOptions,
    AssistantMessage,
    TextBlock,
    ToolUseBlock,
)


class ClaudeSlackApp:
    """
    Slack bot that integrates with Claude Code SDK to respond to user mentions.
    Provides intelligent conversation capabilities through Claude AI.
    """

    def __init__(self, config):
        """
        Initialize the Slack bot with configuration settings.

        Args:
            config (dict): Configuration dictionary loaded from YAML file
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        self.logger.info("Initializing ClaudeSlackApp...")

        # Initialize Claude Code SDK options
        bot_config = config.get("bot", {})

        self.logger.info(f"Configurations: {bot_config}")
        self.claude_options = ClaudeCodeOptions(
            system_prompt=bot_config.get(
                "system_prompt", "You are a helpful Slack bot."
            ),
            allowed_tools=bot_config.get("allowed_tools", []),
            mcp_servers=bot_config.get("mcp_servers", []),
            max_turns=bot_config.get("max_turns", None),
        )

        self.output_tool_use = bot_config.get("output_tool_use", False)

        # Initialize Slack Bolt app
        slack_config = config["slack"]
        self.app = App(
            token=slack_config["bot_token"],
            signing_secret=slack_config["signing_secret"],
        )

        # Register event handlers
        self.app.event("app_mention")(self.handle_mention)
        self.app.event("message")(self.handle_message)

        # Initialize Socket Mode handler
        self.handler = SocketModeHandler(self.app, slack_config["app_token"])

    def handle_mention(self, event, say, client):
        """
        Handle app mention events.

        Args:
            event: Slack event object
            say: Function to send response
            client: Slack Web API client
        """
        try:
            self.logger.info(f"Received mention: {event}")

            # Extract user content by removing bot mention
            user_content = event["text"]
            # Remove bot mention (format: <@USER_ID>)
            import re

            user_content = re.sub(r"<@[A-Z0-9]+>", "", user_content).strip()

            if not user_content:
                say(
                    text=self.config["messages"]["empty_message"], thread_ts=event["ts"]
                )
                return

            # Send immediate "processing" response
            processing_response = say(
                text=self.config["messages"]["processing_message"],
                thread_ts=event["ts"],
            )

            # Get the timestamp of the message we just sent
            processing_ts = processing_response["ts"]

            try:
                # Process with Claude
                response_text = self._process_with_claude(user_content)

                # Update the processing message with the actual response
                client.chat_update(
                    channel=event["channel"], ts=processing_ts, text=response_text
                )

            except Exception as claude_error:
                self.logger.error(f"Error processing with Claude: {claude_error}")
                # Update with error message
                client.chat_update(
                    channel=event["channel"],
                    ts=processing_ts,
                    text=self.config["messages"]["general_error"],
                )

        except Exception as e:
            self.logger.error(f"Error in handle_mention: {e}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            say(text=self.config["messages"]["general_error"], thread_ts=event["ts"])

    def handle_message(self, event, say, client):
        """
        Handle direct message events.

        Args:
            event: Slack event object
            say: Function to send response
            client: Slack Web API client
        """
        try:
            # Only handle direct messages, ignore channel messages and bot messages
            if (
                event.get("channel_type") == "im"
                and event.get("subtype") != "bot_message"
                and "bot_id" not in event
            ):
                self.logger.info(f"Received DM: {event}")

                user_content = event["text"].strip()
                if not user_content:
                    say(self.config["messages"]["empty_message"])
                    return

                # Send immediate "processing" response
                processing_response = say(self.config["messages"]["processing_message"])
                processing_ts = processing_response["ts"]

                try:
                    # Process with Claude
                    response_text = self._process_with_claude(user_content)

                    # Update the processing message with the actual response
                    client.chat_update(
                        channel=event["channel"], ts=processing_ts, text=response_text
                    )

                except Exception as claude_error:
                    self.logger.error(f"Error processing with Claude: {claude_error}")
                    # Update with error message
                    client.chat_update(
                        channel=event["channel"],
                        ts=processing_ts,
                        text=self.config["messages"]["general_error"],
                    )

        except Exception as e:
            self.logger.error(f"Error in handle_message: {e}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            say(self.config["messages"]["general_error"])

    def _process_with_claude(self, user_content):
        """
        Process user message with Claude and return response.

        Args:
            user_content (str): User's message content

        Returns:
            str: Formatted response text
        """
        try:
            responses = []
            self.logger.info(f"Processing message: {user_content}")

            # Query Claude Code SDK - Note: this is async but we're in sync context
            # We need to handle this properly
            import asyncio

            async def get_claude_response():
                responses = []
                async for response in query(
                    prompt=user_content, options=self.claude_options
                ):
                    self.logger.info(f"Received response type: {type(response)}")
                    if isinstance(response, AssistantMessage):
                        for block in response.content:
                            if isinstance(block, TextBlock):
                                responses.append(block.text)
                            elif (
                                isinstance(block, ToolUseBlock) and self.output_tool_use
                            ):
                                if block.name == "Bash":
                                    responses.append(f"*{block.name}*")
                                    responses.append(
                                        f"```\n$ {block.input['command']} # {block.input.get('description')}\n```"
                                    )
                                else:
                                    responses.append(f"*{block.name}*")
                                    responses.append(
                                        f"```\n{json.dumps(block.input, indent=2, ensure_ascii=False)}\n```"
                                    )
                return responses

            # Run async function in current thread
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            responses = loop.run_until_complete(get_claude_response())

            # Format response
            response_text = "\n".join(responses) if responses else ""

            if response_text and len(response_text) > 4000:
                return self.config["messages"]["long_response_error"]
            elif len(response_text) == 0:
                return self.config["messages"]["empty_response"]
            else:
                return response_text

        except Exception as e:
            self.logger.error(f"Error processing with Claude: {e}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return self.config["messages"]["general_error"]

    def start(self):
        """
        Start the Slack bot.
        """
        self.logger.info("Starting Slack bot with Socket Mode...")
        self.handler.start()


def setup_logging(log_level):
    """
    Configure logging system.

    Args:
        log_level (str): Logging level
    """
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        force=True,
    )

    # Set Slack SDK logging to INFO to reduce noise
    logging.getLogger("slack_bolt").setLevel(logging.INFO)


def load_config():
    """
    Load configuration from YAML file.

    Returns:
        dict: Configuration dictionary or None if loading fails
    """
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    logger = logging.getLogger(__name__)

    try:
        with open(config_path, "r", encoding="utf-8") as file:
            config = yaml.safe_load(file)
        return config
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_path}")
        logger.error("Please create config.yaml based on config.example.yaml")
        return None
    except yaml.YAMLError as e:
        logger.error(f"Failed to load YAML configuration file: {e}")
        return None


def main():
    """
    Main entry point for the Slack bot application.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Claude Code Slack Agent")
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging level (default: INFO)",
    )
    args = parser.parse_args()

    # Set up logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    logger.info(f"Starting application with log level: {args.log_level}")

    # Load configuration
    config = load_config()
    if not config:
        logger.error("Failed to load configuration. Please check config.yaml.")
        return

    logger.info("Configuration loaded successfully")

    # Set ANTHROPIC_API_KEY environment variable if configured
    if config.get("claude_code") and config["claude_code"].get("api_key"):
        os.environ["ANTHROPIC_API_KEY"] = config["claude_code"]["api_key"]

    # Validate Slack tokens
    logger.info("Validating tokens...")
    slack_config = config.get("slack", {})

    required_tokens = ["bot_token", "app_token", "signing_secret"]
    for token_name in required_tokens:
        token_value = slack_config.get(token_name)
        if not token_value or token_value.startswith("your_slack_"):
            logger.error(f"Slack {token_name} is not configured in config.yaml")
            return

    logger.info("Tokens validated successfully")

    # Create and start the bot
    try:
        bot = ClaudeSlackApp(config)
        logger.info("Bot created successfully")
        bot.start()
    except KeyboardInterrupt:
        logger.info("Stopping bot...")
    except Exception as e:
        logger.error(f"Error occurred while running bot: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise


if __name__ == "__main__":
    main()
