import chainlit as cl
import os
import asyncio
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.core.credentials import AccessToken, TokenCredential
from azure.identity import DefaultAzureCredential
import logging
import time
from typing import Any

class APIKeyCredential(TokenCredential):
    """Custom credential that uses an API key as a Bearer token"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def get_token(self, *scopes: str, **kwargs: Any) -> AccessToken:
        # Return the API key as a Bearer token
        # Expiry time is set far in the future since API keys don't typically expire
        import time
        return AccessToken(self.api_key, int(time.time()) + 3600)  # 1 hour from now

# Configure logging - set to WARNING to reduce verbose output
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# Suppress Azure SDK verbose logging
logging.getLogger('azure').setLevel(logging.WARNING)
logging.getLogger('azure.core').setLevel(logging.WARNING)
logging.getLogger('azure.ai').setLevel(logging.WARNING)

# Load environment variables
load_dotenv()

# Configuration from environment variables
AZURE_AI_FOUNDRY_ENDPOINT = os.getenv("AZURE_AI_FOUNDRY_ENDPOINT")
AZURE_AI_FOUNDRY_API_KEY = os.getenv("AZURE_AI_FOUNDRY_API_KEY")
AZURE_AI_FOUNDRY_AGENT_ID = os.getenv("AZURE_AI_FOUNDRY_AGENT_ID")

# Validate required environment variables
if not all([AZURE_AI_FOUNDRY_ENDPOINT, AZURE_AI_FOUNDRY_API_KEY, AZURE_AI_FOUNDRY_AGENT_ID]):
    raise ValueError(
        "Missing required environment variables. Please ensure you have set:\n"
        "- AZURE_AI_FOUNDRY_ENDPOINT\n"
        "- AZURE_AI_FOUNDRY_API_KEY\n"
        "- AZURE_AI_FOUNDRY_AGENT_ID"
    )

# Initialize Azure AI Projects client
try:
    # Try with DefaultAzureCredential first (recommended approach)
    try:
        credential = DefaultAzureCredential()
        project_client = AIProjectClient(endpoint=AZURE_AI_FOUNDRY_ENDPOINT, credential=credential)
        print("✅ Connected to Azure AI Foundry")
    except Exception as e:
        # Fallback to API key credential
        print("🔄 Trying alternative authentication...")
        credential = APIKeyCredential(AZURE_AI_FOUNDRY_API_KEY)
        project_client = AIProjectClient(endpoint=AZURE_AI_FOUNDRY_ENDPOINT, credential=credential)
        print("✅ Connected to Azure AI Foundry")
        
except Exception as e:
    logger.error(f"Failed to initialize Azure AI Projects client: {e}")
    raise

@cl.on_chat_start
async def start():
    """Initialize a new chat session with Azure AI Foundry agent"""
    try:
        # Create a new thread for this conversation
        thread = project_client.agents.threads.create()
        
        # Store the thread ID in the user session
        cl.user_session.set("thread_id", thread.id)
        
        # Send welcome message
        welcome_message = """# 🤖 Welcome to Azure AI Foundry Chat! 

You're now connected to an intelligent AI agent powered by **Azure AI Foundry**. 


## Getting Started
Simply type your question or request below and I'll respond with helpful, detailed information.

**Ready to chat? Ask me anything! 🚀**"""
        
        await cl.Message(content=welcome_message).send()
        
    except Exception as e:
        error_msg = f"""# ❌ Connection Error

**Failed to initialize chat session**

```
{str(e)}
```

Please check your Azure AI Foundry configuration and try again."""
        await cl.Message(content=error_msg).send()

@cl.on_message
async def handle_message(message: cl.Message):
    """Handle incoming user messages and get responses from Azure AI Foundry agent"""
    try:
        # Get the thread ID from user session
        thread_id = cl.user_session.get("thread_id")
        if not thread_id:
            error_msg = """# ⚠️ Session Error

**Chat session not properly initialized**

Please refresh the page and try again."""
            await cl.Message(content=error_msg).send()
            return
        
        # Show typing indicator
        async with cl.Step(name="🤔 Processing your request...") as step:
            # Send user message to the thread
            project_client.agents.messages.create(
                thread_id=thread_id,
                role="user",
                content=message.content
            )
            
            # Create and run the agent
            run = project_client.agents.runs.create(
                thread_id=thread_id,
                agent_id=AZURE_AI_FOUNDRY_AGENT_ID
            )
            
            # Wait for the run to complete
            run = await wait_for_run_completion(thread_id, run.id)
            
            if run.status == "completed":
                # Get the latest assistant message
                try:
                    response_text = project_client.agents.messages.get_last_message_text_by_role(
                        thread_id=thread_id,
                        role="assistant"
                    )
                    if response_text:
                        step.output = "✅ Response ready"
                        # Clean and format the response
                        formatted_response = format_agent_response(response_text)
                        await cl.Message(content=formatted_response).send()
                        return
                except Exception as e:
                    pass  # Continue to fallback method
                
                # Fallback: Get all messages and find the assistant response
                messages = project_client.agents.messages.list(thread_id=thread_id)
                messages_list = list(messages)
                
                for msg in messages_list:
                    if msg.role == "assistant" and msg.created_at >= run.created_at:
                        response_text = extract_message_content(msg)
                        if response_text:
                            step.output = "✅ Response ready"
                            # Clean and format the response
                            formatted_response = format_agent_response(response_text)
                            await cl.Message(content=formatted_response).send()
                            return
                
                # If no response found
                no_response_msg = """## 🤔 No Response

The agent processed your message but didn't provide a response. 

**Please try:**
- Rephrasing your question
- Being more specific about what you need
- Asking a different question"""
                await cl.Message(content=no_response_msg).send()
                
            elif run.status == "failed":
                error_details = getattr(run, 'last_error', {})
                error_message = error_details.get('message', 'Unknown error') if error_details else 'Unknown error'
                failed_msg = f"""## ❌ Processing Failed

**The agent encountered an error while processing your message:**

```
{error_message}
```

Please try rephrasing your question or ask something else."""
                await cl.Message(content=failed_msg).send()
                
            else:
                status_msg = f"""## ❓ Unexpected Status

**The agent run completed with status:** `{run.status}`

This is unusual. Please try sending your message again."""
                await cl.Message(content=status_msg).send()
            
    except Exception as e:
        error_msg = f"""## ❌ Processing Error

**An error occurred while processing your message:**

```
{str(e)}
```

Please try again or rephrase your question."""
        await cl.Message(content=error_msg).send()

async def wait_for_run_completion(thread_id: str, run_id: str, max_wait_time: int = 60):
    """Wait for the agent run to complete with timeout"""
    start_time = time.time()
    
    while True:
        run = project_client.agents.runs.get(thread_id=thread_id, run_id=run_id)
        
        if run.status in ["completed", "failed", "cancelled", "expired"]:
            return run
        
        # Check timeout
        if time.time() - start_time > max_wait_time:
            # Cancel the run if possible
            try:
                project_client.agents.runs.cancel(thread_id=thread_id, run_id=run_id)
            except:
                pass
            raise TimeoutError(f"Agent response timed out after {max_wait_time} seconds")
        
        # Wait before checking again
        await asyncio.sleep(1)

def extract_message_content(message) -> str:
    """Extract text content from a thread message"""
    try:
        if hasattr(message, 'content') and message.content:
            for content_item in message.content:
                if hasattr(content_item, 'text') and hasattr(content_item.text, 'value'):
                    return content_item.text.value
                elif hasattr(content_item, 'type') and content_item.type == 'text':
                    return content_item.text.value
        return None
    except Exception as e:
        return None

def format_agent_response(response_text: str) -> str:
    """Format the agent response for better readability"""
    if not response_text:
        return "## 🤖 Agent Response\n\nNo response content available."
    
    # Clean up the response text
    response_text = response_text.strip()
    
    # If the response doesn't start with a markdown header, add one
    if not response_text.startswith('#'):
        # Check if it's a code block or technical response
        if '```' in response_text or response_text.startswith('def ') or response_text.startswith('class '):
            formatted_response = f"## 🤖 Agent Response\n\n{response_text}"
        else:
            # Regular text response
            formatted_response = f"## 🤖 Agent Response\n\n{response_text}"
    else:
        formatted_response = response_text
    
    return formatted_response

@cl.on_chat_end
async def end():
    """Clean up when chat session ends"""
    thread_id = cl.user_session.get("thread_id")
    if thread_id:
        print(f"💬 Chat session ended for thread: {thread_id}")
        # Note: We don't delete the thread here as it might be useful for debugging
        # In production, you might want to implement thread cleanup based on your needs
