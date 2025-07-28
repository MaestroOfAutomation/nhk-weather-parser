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
   git clone https://github.com/yourusername/nhk-japan-weather-parser.git
   cd nhk-japan-weather-parser
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install camoufox:
   ```bash
   pip install camoufox
   ```

4. Create and configure your `config.json` file

5. Run the application:
   ```bash
   python run.py
   ```

### Docker Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/nhk-japan-weather-parser.git
   cd nhk-japan-weather-parser
   ```

2. Create and configure your `config.json` file

3. Build and run the Docker container:
   ```bash
   docker build -t nhk-japan-weather-parser .
   docker run --rm -v $(pwd)/config.json:/app/config.json nhk-japan-weather-parser
   ```

## GitHub Actions Deployment

This project includes two GitHub Actions workflows:

### Build and Push Docker Image

This workflow builds and pushes the Docker image to GitHub Container Registry:

1. Fork this repository
2. Go to the "Actions" tab in your repository
3. Select the "Build and Deploy Docker Image" workflow
4. Click "Run workflow"
5. Enter a tag for the Docker image (default: "latest")
6. Click "Run workflow" again

The Docker image will be built and pushed to GitHub Container Registry.

### Self-Hosted Deployment

This workflow deploys the application on a self-hosted runner using Docker Compose:

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
- Build the Docker image using Docker Compose
- Create a config.json file from your GitHub variable
- Deploy the application using Docker Compose

You can copy the `example.config.json` file to `config.json` and fill in your actual values before creating the GitHub variable.

## Setting Up as a Cron Job

### Using Docker

```bash
# Run daily at 8:00 AM
0 8 * * * docker run --rm -v /path/to/config.json:/app/config.json ghcr.io/yourusername/nhk-japan-weather-parser:latest
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

## License

MIT