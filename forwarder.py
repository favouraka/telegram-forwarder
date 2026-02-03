#!/usr/bin/env python3
"""
Telegram Forwarder - Memory-optimized version
- Reduced logging overhead
- Lazy cleanup (only when needed)
- Optimized for ~25-30 MB memory usage
"""

import os
import sys
import logging
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError
from telethon.tl.types import MessageMediaPhoto

# Configure logging - WARNING level only (less overhead)
logging.basicConfig(
    level=logging.WARNING,  # Reduced from INFO
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('forwarder.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Secure permissions for session directory
SESSION_DIR = Path.home() / '.telegram-forwarder'
SESSION_DIR.mkdir(mode=0o700, exist_ok=True)
SESSION_FILE = SESSION_DIR / 'secure_session'

# Temp directory for downloaded images
TEMP_DIR = Path('/tmp/telegram-forwarder')
TEMP_DIR.mkdir(mode=0o700, exist_ok=True)

_cleanup_counter = 0
CLEANUP_INTERVAL = 20  # Cleanup every 20 messages

def cleanup_old_files():
    """Remove files older than 3 hours from temp directory."""
    try:
        cutoff = datetime.now() - timedelta(hours=3)
        removed = 0
        for file in TEMP_DIR.glob('*'):
            if file.is_file():
                file_mtime = datetime.fromtimestamp(file.stat().st_mtime)
                if file_mtime < cutoff:
                    file.unlink()
                    removed += 1
        if removed > 0:
            logger.info(f"Cleaned up {removed} old file(s)")
    except Exception as e:
        logger.error(f"Error cleaning up temp files: {e}")

def validate_config():
    """Validate required environment variables."""
    required = ['TELEGRAM_API_ID', 'TELEGRAM_API_HASH']
    missing = [var for var in required if not os.getenv(var)]

    if missing:
        logger.error(f"Missing required environment variables: {', '.join(missing)}")
        logger.error("Please set them in config.env")
        sys.exit(1)

    api_id = os.getenv('TELEGRAM_API_ID')
    if not api_id.isdigit():
        logger.error("TELEGRAM_API_ID must be a number")
        sys.exit(1)

    return int(api_id), os.getenv('TELEGRAM_API_HASH')

async def list_groups(client):
    """List all groups the user is a member of."""
    logger.info("Fetching your groups...")

    dialogs = await client.get_dialogs()
    groups = [d for d in dialogs if d.is_group or d.is_channel]

    if not groups:
        logger.info("No groups found")
        return

    print("\n" + "=" * 70)
    print("Groups you're a member of:")
    print("=" * 70)

    for idx, dialog in enumerate(groups, 1):
        print(f"\n{idx}. {dialog.name}")
        print(f"   ID: {dialog.id}")
        print(f"   Type: {'Channel' if dialog.is_channel else 'Group'}")

    print(f"\n{'=' * 70}")
    print(f"Total: {len(groups)} group(s)")
    print("=" * 70)
    print("\n💡 Add the group IDs you want to monitor to config.env")

async def download_image_if_needed(client, message):
    """Download image if it's a photo media. Returns file path or None."""
    if not message.media:
        return None

    # Only download photos
    if isinstance(message.media, MessageMediaPhoto):
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            filename = TEMP_DIR / f"img_{timestamp}.jpg"

            await client.download_media(message.media, filename)
            return str(filename)
        except Exception as e:
            logger.error(f"Failed to download image: {e}")
            return None

    return None

async def send_test_message(client):
    """Send a test message to the destination group."""
    dest_group_id = os.getenv('DESTINATION_GROUP_ID', '')

    if not dest_group_id:
        logger.error("DESTINATION_GROUP_ID must be set")
        sys.exit(1)

    try:
        dest_group = int(dest_group_id)
    except ValueError:
        logger.error("Destination group ID must be an integer")
        sys.exit(1)

    logger.info(f"Sending test message to group ID: {dest_group}")

    try:
        await client.send_message(
            dest_group,
            message="🧪 Test message from Telegram Forwarder\n\n✅ If you see this, the destination group is working correctly!"
        )
        logger.warning("✅ Test message sent successfully!")
        print("\n✅ Test message sent! Check your destination group.")
    except Exception as e:
        logger.error(f"❌ Failed to send test message: {e}")
        print(f"\n❌ Error: {e}")
        print("\nThis usually means:")
        print("  • You don't have access to the destination group")
        print("  • The group ID is incorrect")
        print("  • The group restricted posting permissions")

async def start_forwarding(client):
    """Start forwarding messages from source to destination."""
    source_groups_str = os.getenv('SOURCE_GROUP_IDS', '')
    dest_group_id = os.getenv('DESTINATION_GROUP_ID', '')

    if not source_groups_str or not dest_group_id:
        logger.error("SOURCE_GROUP_IDS and DESTINATION_GROUP_ID must be set")
        sys.exit(1)

    try:
        source_groups = [int(gid.strip()) for gid in source_groups_str.split(',')]
        dest_group = int(dest_group_id)
    except ValueError:
        logger.error("Group IDs must be integers")
        sys.exit(1)

    logger.info(f"Monitoring {len(source_groups)} group(s)")
    logger.info(f"Forwarding to group ID: {dest_group}")
    logger.warning("✅ Forwarding active. Press Ctrl+C to stop")

    global _cleanup_counter

    @client.on(events.NewMessage(chats=source_groups))
    async def handler(event):
        try:
            global _cleanup_counter
            _cleanup_counter += 1

            # Lazy cleanup every 20 messages
            if _cleanup_counter >= CLEANUP_INTERVAL:
                cleanup_old_files()
                _cleanup_counter = 0

            message = event.message
            sender = await message.get_sender()
            sender_name = getattr(sender, 'first_name', 'Unknown')

            chat = await message.get_chat()
            chat_name = getattr(chat, 'title', f'Group {chat.id}')

            # Download image if needed
            image_path = await download_image_if_needed(client, message)

            # Build message
            message_text = f"📨 From {chat_name}\n👤 {sender_name}:\n\n"
            if message.text:
                message_text += message.text

            # Send
            await client.send_message(
                dest_group,
                message=message_text,
                file=image_path if image_path else None
            )

            logger.info(f"Forwarded from {chat_name}")

        except Exception as e:
            logger.error(f"Error: {e}")

    await client.run_until_disconnected()

async def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 forwarder.py list-groups      - List all your groups")
        print("  python3 forwarder.py forward           - Start forwarding messages")
        print("  python3 forwarder.py test              - Send test message to destination")
        sys.exit(1)

    command = sys.argv[1]

    load_dotenv('config.env')
    api_id, api_hash = validate_config()

    # Create client with optimized settings
    client = TelegramClient(
        str(SESSION_FILE),
        api_id,
        api_hash
    )

    await client.connect()

    if not await client.is_user_authorized():
        phone = os.getenv('PHONE_NUMBER', '')
        if not phone:
            print("Enter your phone number:")
            phone = input("> ").strip()

        await client.send_code_request(phone)

        print("\nEnter verification code:")
        code = input("> ").strip()

        try:
            # Try to sign in with verification code
            await client.sign_in(phone, code)
        except SessionPasswordNeededError:
            # 2FA password required - prompt interactively
            print("\n🔐 Two-factor authentication enabled")
            print("Enter your 2FA password (hint: check your cloud password):")
            password = input("> ").strip()

            try:
                await client.sign_in(password=password)
            except Exception as e:
                logger.error(f"❌ Failed to authenticate with 2FA password: {e}")
                print(f"\n❌ Error: {e}")
                print("Please check your 2FA password and try again.")
                sys.exit(1)
        except Exception as e:
            logger.error(f"❌ Sign in failed: {e}")
            print(f"\n❌ Error: {e}")
            sys.exit(1)

        logger.warning("✅ Authentication successful")

    try:
        if command == "list-groups":
            await list_groups(client)
        elif command == "forward":
            await start_forwarding(client)
        elif command == "test":
            await send_test_message(client)
        else:
            logger.error(f"Unknown command: {command}")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)
    finally:
        await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
