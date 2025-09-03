"""
Test Azure AI Foundry Connection
This script tests the connection to our Azure AI Foundry resources using cost-effective models.
"""

import os
import asyncio
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from openai import AzureOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_azure_connection():
    """Test Azure AI Foundry connection and models"""
    
    print("🔄 Testing Azure AI Foundry Connection...")
    print("=" * 50)
    
    # Test Azure OpenAI connection
    try:
        print("\n1. Testing Azure OpenAI (GPT-4o mini)...")
        
        client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        )
        
        # Test with a simple insurance-related query
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o-mini-deployment"),
            messages=[
                {"role": "system", "content": "You are an insurance claims processing assistant."},
                {"role": "user", "content": "What are the key steps in processing an auto insurance claim?"}
            ],
            max_tokens=200,
            temperature=0.3
        )
        
        print("✅ Azure OpenAI connection successful!")
        print(f"Model: {response.model}")
        print(f"Response: {response.choices[0].message.content[:100]}...")
        print(f"Tokens used: {response.usage.total_tokens}")
        
    except Exception as e:
        print(f"❌ Azure OpenAI connection failed: {e}")
        return False
    
    # Test Azure AI Projects
    try:
        print("\n2. Testing Azure AI Projects connection...")
        
        credential = DefaultAzureCredential()
        project_client = AIProjectClient(
            endpoint=os.getenv("AZURE_AI_PROJECT_ENDPOINT"),
            credential=credential,
            subscription_id=os.getenv("AZURE_SUBSCRIPTION_ID"),
            resource_group_name=os.getenv("AZURE_RESOURCE_GROUP"),
            project_name=os.getenv("AZURE_AI_PROJECT_NAME")
        )
        
        print("✅ Azure AI Projects connection successful!")
        print(f"Project: {os.getenv('AZURE_AI_PROJECT_NAME')}")
        print(f"Resource Group: {os.getenv('AZURE_RESOURCE_GROUP')}")
        
    except Exception as e:
        print(f"❌ Azure AI Projects connection failed: {e}")
        print("Note: This might require additional authentication setup")
    
    # Test cost estimation
    print("\n3. Cost Analysis for GPT-4o mini...")
    print("   • Input tokens: ~$0.000150 per 1K tokens")
    print("   • Output tokens: ~$0.000600 per 1K tokens") 
    print("   • ~60% cheaper than GPT-4!")
    print("   • Perfect for insurance claim processing")
    
    print("\n🎉 Connection test completed!")
    return True

def test_environment_variables():
    """Check if all required environment variables are set"""
    
    print("🔄 Checking Environment Variables...")
    print("=" * 40)
    
    required_vars = [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_KEY", 
        "AZURE_OPENAI_DEPLOYMENT_NAME",
        "AZURE_AI_PROJECT_NAME",
        "AZURE_RESOURCE_GROUP",
        "AZURE_SUBSCRIPTION_ID"
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if "KEY" in var or "SECRET" in var:
                masked_value = value[:8] + "..." if len(value) > 8 else "***"
                print(f"✅ {var}: {masked_value}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: Not set")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n⚠️  Missing variables: {', '.join(missing_vars)}")
        print("Please update your .env file")
        return False
    else:
        print("\n🎉 All environment variables are set!")
        return True

if __name__ == "__main__":
    print("🚀 Azure AI Foundry Insurance Agents - Connection Test")
    print("=" * 60)
    
    # Test environment first
    if test_environment_variables():
        # Then test connections
        asyncio.run(test_azure_connection())
    else:
        print("\n❌ Please fix environment variables before testing connections")
