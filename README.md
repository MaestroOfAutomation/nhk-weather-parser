# NHK Japan Weather Parser

A tool that scrapes weather data from the NHK Japan weather website, generates a summary using AI, and posts it to a Telegram channel.

## Features

- Scrapes weather data from NHK Japan website
- Translates Japanese city names to Russian
- Takes a screenshot of the weather map
- Generates a weather summary using DeepSeek AI
- Posts the summary and screenshot to a Telegram channel
- Runs as a scheduled task (cron job)

## Project Structure

The project is organized into the following structure:

```
nhk_japan_weather_parser/
├── nhk_weather/              # Main package directory
│   ├── config/               # Configuration module
│   │   ├── __init__.py
│   │   └── config.py         # Configuration manager
│   ├── core/                 # Core functionality
│   │   ├── __init__.py
│   │   └── models.py         # Data models
│   ├── services/             # Service modules
│   │   ├── __init__.py
│   │   ├── ai.py             # DeepSeek AI service
│   │   ├── browser.py        # Browser scraping service
│   │   └── telegram.py       # Telegram messaging service
│   ├── utils/                # Utility functions
│   │   └── __init__.py
│   └── __init__.py
├── run.py                    # Entry point script
├── config.json               # Configuration file
├── example.config.json       # Example configuration file
├── requirements.txt          # Dependencies
├── Dockerfile                # Docker configuration
└── README.md                 # Documentation
```

## Requirements

- Python 3.11+
- Docker (for containerized deployment)
- DeepSeek API key
- Telegram bot token and chat ID

## Configuration

Create a `config.json` file in the project root with the following structure:

```json
{
  "deepseek": {
    "api_key": "your-deepseek-api-key",
    "api_url": "https://api.deepseek.com/chat/completions",
    "model": "deepseek-chat"
  },
  "telegram": {
    "bot_token": "your-telegram-bot-token",
    "chat_id": "your-telegram-chat-id"
  },
  "nhk": {
    "url": "https://www.nhk.or.jp/kishou-saigai/",
    "map_selector": ".theWeatherForecastWeeklyMap"
  }
}
```

Alternatively, you can set the following environment variables:

- `DEEPSEEK_API_KEY`: Your DeepSeek API key
- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
- `TELEGRAM_CHAT_ID`: Your Telegram chat ID
- `CONFIG_PATH`: Path to your config file (optional)

## Installation

### Local Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/username/nhk-japan-weather-parser.git
   cd nhk-japan-weather-parser
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install Playwright browsers:
   ```bash
   python -m playwright install --with-deps firefox
   ```

4. Create and configure your `config.json` file

5. Run the application:
   ```bash
   python run.py
   ```

### Docker Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/username/nhk-japan-weather-parser.git
   cd nhk-japan-weather-parser
   ```

2. Create and configure your `config.json` file

3. Build and run the Docker container:
   ```bash
   docker build -t nhk-japan-weather-parser .
   docker run --rm -v $(pwd)/config.json:/app/config.json nhk-japan-weather-parser
   ```

## GitHub Actions Deployment

This project includes a GitHub Actions workflow for deployment:

### Self-Hosted Deployment

This workflow deploys the application on a self-hosted runner using Docker:

1. Set up a self-hosted GitHub Actions runner on your server
2. Create a GitHub repository variable named `CONFIG` containing your entire config.json content:
   - Go to your repository settings
   - Select "Secrets and variables" → "Actions"
   - Go to the "Variables" tab
   - Click "New repository variable"
   - Name: `CONFIG`
   - Value: Copy the entire content of your config.json file
3. Go to the "Actions" tab in your repository
4. Select the "Deploy bot" workflow
5. Click "Run workflow"

The workflow will:
- Check out the code
- Build the Docker image
- Create a config.json file from your GitHub variable
- Stop and remove any existing container
- Deploy the application using Docker

You can copy the `example.config.json` file to `config.json` and fill in your actual values before creating the GitHub variable.

## Setting Up as a Cron Job

### Using Docker

```bash
# Run daily at 8:00 AM
0 8 * * * docker run --rm -v /path/to/config.json:/app/config.json ghcr.io/username/nhk-japan-weather-parser:latest
```

### Using systemd timer (Linux)

1. Create a service file `/etc/systemd/system/nhk-weather.service`:
   ```
   [Unit]
   Description=NHK Japan Weather Parser
   After=network.target

   [Service]
   Type=oneshot
   ExecStart=/usr/bin/python /path/to/nhk-japan-weather-parser/run.py
   WorkingDirectory=/path/to/nhk-japan-weather-parser
   User=yourusername

   [Install]
   WantedBy=multi-user.target
   ```

2. Create a timer file `/etc/systemd/system/nhk-weather.timer`:
   ```
   [Unit]
   Description=Run NHK Japan Weather Parser daily

   [Timer]
   OnCalendar=*-*-* 08:00:00
   Persistent=true

   [Install]
   WantedBy=timers.target
   ```

3. Enable and start the timer:
   ```bash
   sudo systemctl enable nhk-weather.timer
   sudo systemctl start nhk-weather.timer
   ```

## How It Works

1. **Web Scraping**: The application uses Playwright to scrape weather data from the NHK Japan weather website. It captures information about cities, temperatures, and weather conditions.

2. **Translation**: Japanese city names are translated to Russian using DeepSeek AI. The application maintains a dictionary of common city translations and uses AI for any unknown cities.

3. **Weather Summary**: The application generates a concise weather summary in Russian using DeepSeek AI. The summary includes:
   - Current date
   - Weather conditions in key cities (especially Tokyo, Sapporo, and southern cities)
   - Maximum temperatures in Celsius
   - Notable weather phenomena (rain, storms, snow, etc.)
   - Appropriate emojis

4. **Telegram Posting**: The weather summary and a screenshot of the weather map are posted to a Telegram channel using the Telegram Bot API.

## AI Integration

This project uses DeepSeek AI for two main purposes:

1. **Translation**: Converting Japanese city names to Russian
2. **Weather Summary Generation**: Creating natural language summaries of weather data

The DeepSeek API is used with specific prompts designed to:
- Generate accurate translations of Japanese city names
- Create concise, informative weather summaries in Russian
- Rephrase summaries for better readability

## Troubleshooting

### Common Issues

1. **No weather data found**
   - Check if the NHK website structure has changed
   - Verify that the CSS selector in config.json is correct
   - Increase the wait time in browser.py if the page is loading slowly

2. **Translation issues**
   - Verify your DeepSeek API key is valid
   - Check the DeepSeek API URL in your configuration
   - Ensure you have sufficient API credits

3. **Telegram posting fails**
   - Verify your bot token is correct
   - Ensure the bot has permission to post in the specified chat
   - Check if the message or caption exceeds Telegram's length limits

### Debugging

The application uses the loguru library for logging. To enable more detailed logs, you can set the `LOGURU_LEVEL` environment variable:

```bash
LOGURU_LEVEL=DEBUG python run.py
```

## Contributing

Contributions are welcome! Here's how you can contribute:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

Please make sure your code follows the existing style and includes appropriate tests.

## Recent Updates

- **July 2025**: Updated README with more detailed documentation
- Added troubleshooting section
- Improved installation instructions
- Enhanced AI integration documentation

## License

MIT