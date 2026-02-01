# Telegram Forwarder - Secure Userbot

A secure Telegram userbot for forwarding messages from private groups to an aggregator group.

## 🔒 Security Features

- **Credentials in environment only** — Never hardcoded
- **Restricted file permissions** — Config files 0600, session dir 0700
- **Runs as unprivileged user** — No root access needed
- **No open ports** — Outbound connections only
- **Isolated session** — Won't interfere with other services
- **Sanitized logging** — No sensitive data in logs

## 📋 Prerequisites

- Python 3.8+
- pip (python3-pip)
- Telegram account (to get API credentials)

## 🚀 Quick Start (Local)

### 1. Install pip

```bash
sudo apt-get install -y python3-pip
```

### 2. Navigate to project

```bash
cd ~/telegram-forwarder-py
```

### 3. Create virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Get Telegram API credentials

1. Go to https://my.telegram.org
2. Sign in with your phone number
3. Go to "API development tools"
4. Create a new app
5. Copy `api_id` and `api_hash`

### 6. Configure

```bash
nano config.env
```

Add your credentials:
```env
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=your_api_hash_here
PHONE_NUMBER=+234XXXXXXXXXX
```

### 7. Run secure setup

```bash
chmod +x setup.sh
./setup.sh
```

### 8. List your groups

```bash
python3 forwarder.py list-groups
```

First run will ask for:
- Phone number (or use PHONE_NUMBER from config)
- Verification code (sent to Telegram)
- 2FA password (if enabled)

### 9. Start forwarding

1. Update `config.env` with group IDs:
```env
SOURCE_GROUP_IDS=-1001234567890,-1001234567891
DESTINATION_GROUP_ID=-1001234567892
```

2. Run:
```bash
python3 forwarder.py forward
```

## 🌐 Deploy to VPS

### 1. Copy to VPS via Tailnet

```bash
# From your home machine
scp -r ~/telegram-forwarder-py YOUR_VPS_HOST:~/
```

### 2. On VPS: Setup

```bash
cd ~/telegram-forwarder-py
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
./setup.sh
```

### 3. Configure

```bash
nano config.env
# Add your credentials
```

### 4. Test run

```bash
source venv/bin/activate
python3 forwarder.py list-groups
python3 forwarder.py forward
```

### 5. Install as service

Edit `telegram-forwarder.service`:
- Replace `YOUR_USERNAME` with your actual username

```bash
# Install service
sudo cp telegram-forwarder.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable telegram-forwarder
sudo systemctl start telegram-forwarder

# Check status
sudo systemctl status telegram-forwarder

# View logs
sudo journalctl -u telegram-forwarder -f
```

## 🛡️ Security Best Practices

1. **Never commit config.env** — Add to .gitignore
2. **Use strong 2FA** — Enable on your Telegram account
3. **Limit group access** — Only add necessary groups
4. **Monitor logs** — Check forwarder.log regularly
5. **Update dependencies** — `pip install --upgrade -r requirements.txt`
6. **Secure VPS** — Use firewall, fail2ban, etc.

## 📝 Commands

- `python3 forwarder.py list-groups` — List all groups
- `python3 forwarder.py forward` — Start forwarding

## 🔧 Troubleshooting

**Issue: "No module named 'telethon'"**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

**Issue: Permission denied**
```bash
chmod +x forwarder.py setup.sh
./setup.sh
```

**Issue: Service not starting**
```bash
sudo journalctl -u telegram-forwarder -n 50
```

## 📄 Files

- `forwarder.py` — Main script
- `config.env` — Configuration (credentials)
- `requirements.txt` — Python dependencies
- `setup.sh` — Secure setup script
- `telegram-forwarder.service` — systemd service file
- `forwarder.log` — Runtime logs

## ⚠️ Important Notes

- This acts as YOUR account — everything you do appears as you
- You must be a member of all groups you want to monitor
- The destination group must exist before forwarding starts
- Session data is stored in `~/.telegram-forwarder/` (encrypted)
