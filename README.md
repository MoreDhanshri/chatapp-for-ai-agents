# Azure AI Foundry Chainlit Chat Application

A modern yet simple chat application that integrates **Chainlit** with **Azure AI Foundry** agents, providing an intuitive interface for users to interact with intelligent AI assistants.



## 📋 Prerequisites

Before running this application, you need:

1. **Azure AI Foundry Project** with an agent created
2. **Python 3.8+** installed on your system
3. **Azure AI Foundry API credentials**

## 🛠️ Setup Instructions

### 1. Clone or Download the Repository

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your Azure AI Foundry credentials:
   ```env
   AZURE_AI_FOUNDRY_ENDPOINT=https://your-foundry-endpoint.services.ai.azure.com/api/projects/your-project-id
   AZURE_AI_FOUNDRY_API_KEY=your-api-key-here
   AZURE_AI_FOUNDRY_AGENT_ID=asst_your-agent-id-here
   ```

### 4. Get Your Azure AI Foundry Credentials

#### Finding Your Endpoint:
1. Go to [Azure AI Foundry](https://ai.azure.com)
2. Navigate to your project
3. Go to **Settings** → **Project details**
4. Copy the **Project endpoint** (should include `/api/projects/your-project-id`)

#### Getting Your API Key:
1. In Azure AI Foundry, go to **Settings** → **Connections**
2. Find your project connection
3. Copy the **API Key**

#### Finding Your Agent ID:
1. Go to **Agents** section in your Azure AI Foundry project
2. Click on your agent
3. Copy the **Agent ID** (starts with `asst_`)

### 5. Run the Application

```bash
chainlit run chainlit_foundry_chat.py -w
```

The application will start and be available at `http://localhost:8000`

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Chainlit UI   │◄──►│  Python App     │◄──►│ Azure AI Foundry│
│   (Frontend)    │    │   (Backend)     │    │    (AI Agent)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Key Components:

- **Chainlit**: Provides the chat interface and user experience
- **Azure AI Projects SDK**: Handles communication with Azure AI Foundry
- **Thread Management**: Maintains conversation context using Azure AI Foundry threads
- **Async Processing**: Ensures responsive UI during AI processing

## 🔧 Configuration Options

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `AZURE_AI_FOUNDRY_ENDPOINT` | Full endpoint URL including project path | Yes |
| `AZURE_AI_FOUNDRY_API_KEY` | Project-level API key | Yes |
| `AZURE_AI_FOUNDRY_AGENT_ID` | ID of the agent to chat with | Yes |

### Customization

- **Welcome Message**: Edit `chainlit.md` to customize the welcome screen
- **App Behavior**: Modify `chainlit_foundry_chat.py` to change chat logic
- **Styling**: Use Chainlit's theming options to customize appearance

## 🐛 Troubleshooting

### Common Issues:

1. **"Missing environment variables" error**:
   - Ensure all required variables are set in your `.env` file
   - Check that variable names match exactly

2. **"Failed to initialize Azure AI Projects client" error**:
   - Verify your endpoint URL includes the full project path
   - Check that your API key is valid and has proper permissions

3. **"Agent failed to process your message" error**:
   - Ensure your agent ID is correct
   - Check that the agent is deployed and running in Azure AI Foundry

4. **Connection timeout errors**:
   - Check your internet connection
   - Verify Azure AI Foundry service status

### Debug Mode:

Run with debug logging:
```bash
PYTHONPATH=. python -c "import logging; logging.basicConfig(level=logging.DEBUG)" && chainlit run chainlit_foundry_chat.py -w
```


## 🤝 Contributing

Feel free to submit issues, feature requests, or pull requests to improve this application!

## 📄 License

This project is provided as-is for educational and development purposes.

