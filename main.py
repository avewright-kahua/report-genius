import os
from agents import Agent
from agents.azure import AzureOpenAIClient  # or a connector for Azure

# 1. Create the Azure client wrapper
azure_client = AzureOpenAIClient(
    endpoint=os.getenv("AZURE_ENDPOINT"),
    api_key=os.getenv("AZURE_KEY"),
    api_version="2025-01-01-preview",
    model_name="gpt-4o"
)

agent = Agent(
    client=azure_client,
    model="gpt-4o",
    instructions="You are a helpful assistant that can answer questions and help with tasks.",
    verbose=True
)

result = agent.run("Hello, how are you?")
print(result)
