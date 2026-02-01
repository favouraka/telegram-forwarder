#!/bin/bash
# Secure setup script for Telegram Forwarder

set -e

echo "🔒 Telegram Forwarder - Secure Setup"
echo "======================================"

# Create session directory with secure permissions
echo "Setting up secure session directory..."
mkdir -p ~/.telegram-forwarder
chmod 700 ~/.telegram-forwarder

# Set secure permissions on config file
if [ -f "config.env" ]; then
    echo "Securing config file..."
    chmod 600 config.env
fi

# Set executable on script
chmod +x forwarder.py

echo ""
echo "✅ Secure setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit config.env with your credentials"
echo "2. Run: python3 -m venv venv"
echo "3. Run: source venv/bin/activate"
echo "4. Run: pip install -r requirements.txt"
echo "5. Run: python3 forwarder.py list-groups"
