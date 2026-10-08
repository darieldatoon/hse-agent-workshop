terraform {
  required_version = ">= 1.11"

  required_providers {
    langsmith = {
      source  = "langchain-ai/langsmith"
      version = "~> 0.0.16"
    }
  }
}

# Credentials come from LANGSMITH_API_KEY (an org admin key), loaded from ../.env by the mise
# tasks. Never set api_key here.
provider "langsmith" {}
