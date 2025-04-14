# Gmail Manager - AI-Powered Email Assistant

![Gmail Manager Screenshot](https://i.imgur.com/JfQvX9E.png)

## Table of Contents
- [Introduction](#introduction)
- [Features](#features)
- [Technologies Used](#technologies-used)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Screenshots](#screenshots)
- [Contributing](#contributing)
- [License](#license)
- [Developer](#developer)

## Introduction
Gmail Manager is an AI-powered email assistant that helps you efficiently manage your Gmail inbox. Built with Python and Streamlit, it provides powerful tools for email analysis, organization, and automation.

## Features

### 📊 Email Analytics
- View statistics about your email patterns
- See most active senders and categories
- Analyze time-based email distribution

### 🧹 Bulk Email Management
- Delete multiple emails by sender or criteria
- Archive unimportant messages
- Label and categorize emails automatically

### 🤖 AI Assistant
- Natural language commands for email management
- Smart suggestions for inbox organization
- Automated email categorization

### ⚙️ Automation
- Create custom email rules
- Schedule regular cleanup tasks
- Apply rules to incoming emails automatically

### 🔍 Email Insights
- Analyze email importance
- Find unsubscribe opportunities
- Get detailed sender statistics

## Technologies Used
- Python 3.9+
- Streamlit (Frontend)
- Google Gmail API
- LangChain (AI Agent Framework)
- Google Generative AI (Gemini)
- OAuth 2.0 Authentication

## Installation

1. Clone the repository:
```bash
git clone https://github.com/sonu2164/gmail-manager.git
cd gmail-manager
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

1. Set up Google Cloud Project:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable Gmail API
   - Create OAuth 2.0 credentials
   - Download credentials as `client_secret.json` and place in project root

2. Set up Google Generative AI:
   - Get API key from [Google AI Studio](https://makersuite.google.com/)
   - Add to `.env` file:
     ```
     GOOGLE_API_KEY=your_api_key_here
     ```

## Usage

1. Run the application:
```bash
streamlit run main.py
```

2. In the app:
   - Click "Authenticate" in the sidebar
   - Complete the Google OAuth flow
   - Use the AI Assistant or manual tools to manage your emails

### Example Commands:
- "Show me emails from the last 7 days"
- "Unsubscribe from all newsletters"
- "Delete all promotional emails older than 30 days"
- "Create a rule to label all work emails"
- "Analyze my email patterns"

## Screenshots

![Dashboard View](https://i.imgur.com/JfQvX9E.png)
*Dashboard showing email analytics*

![AI Assistant](https://i.imgur.com/XyZ9LmT.png)
*AI Assistant with natural language commands*

![Email Rules](https://i.imgur.com/8kLmV9p.png)
*Creating automated email rules*

## Contributing

Contributions are welcome! Please follow these steps:
1. Fork the repository
2. Create a new branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add some feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Developer
- **Name**: Sonu Singh
- **GitHub**: [sonu2164](https://github.com/sonu2164)
- **Hackathon**: Quira 25 Quest
