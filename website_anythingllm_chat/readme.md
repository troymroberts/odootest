# Odoo LLM Chat Integration

This Odoo module integrates Large Language Models (LLM) with Odoo's native chat system, enabling AI-powered responses in real-time conversations.

## 🚀 Features

- Native integration with Odoo chat
- Real-time LLM responses
- Configurable API endpoints
- Message history tracking
- Per-channel LLM enablement
- Error handling and logging

## 📋 Requirements

- Odoo 17.0
- Python 3.8+
- Active LLM API endpoint
- API key for your LLM service

## 🔧 Installation

1. Clone this repository into your Odoo addons directory:
```bash
git clone https://github.com/your-repo/odoo-llm-chat /path/to/odoo/addons
```

2. Update your Odoo addons list from the Apps menu

3. Install the module by searching for "Odoo LLM Chat Integration"

## ⚙️ Configuration

### 1. System Settings

Navigate to Settings → LLM Chat and configure:
- LLM API URL
- API Key
- Default channel behavior

### 2. Per-Channel Settings

In any chat channel:
- Toggle LLM integration on/off
- Configure channel-specific settings

## 💻 Usage

### Basic Usage

1. Start a chat conversation
2. Type your message
3. Receive AI-powered responses automatically

### Message Management

Access LLM Chat → Messages to:
- View message history
- Check processing status
- Monitor errors

## 🔌 API Integration

### Request Format

```json
{
    "message": "User message",
    "history": [
        {"role": "user", "content": "Previous message"},
        {"role": "assistant", "content": "Previous response"}
    ],
    "channel_id": 123
}
```

### Response Format

```json
{
    "response": "AI response content"
}
```

## 🛠️ Development

### Directory Structure

```
odoo-llm-chat/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── llm_chat.py
│   └── res_config_settings.py
├── controllers/
│   ├── __init__.py
│   └── main.py
├── views/
│   ├── llm_chat_views.xml
│   └── res_config_settings_views.xml
└── security/
    └── ir.model.access.csv
```

### Key Components

- `llm_chat.py`: Core LLM integration logic
- `res_config_settings.py`: Configuration management
- `main.py`: API controller
- `llm_chat_views.xml`: UI components

## 🐛 Troubleshooting

### Common Issues

1. No LLM Response
   - Check API URL configuration
   - Verify API key
   - Review error logs

2. Message Processing Errors
   - Check network connectivity
   - Verify API endpoint
   - Check message format

### Logging

Find logs in:
- Odoo server logs
- LLM message records
- System notifications

## 📝 License

This project is licensed under LGPL-3 - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to your branch
5. Create a Pull Request

## ✨ Support

- Issues: GitHub issue tracker
- Documentation: See `/doc` directory
- Community: Odoo Community Forum

## 📖 Additional Resources

- [Module Documentation](docs/index.md)
- [API Documentation](docs/api.md)
- [Configuration Guide](docs/configuration.md)

---
Made with ❤️ for the Odoo Community