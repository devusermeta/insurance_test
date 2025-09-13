# Communication Agent

The Communication Agent is responsible for sending email notifications about insurance claim decisions using Azure Communication Services.

## Purpose
- Sends email notifications for claim acceptance/denial decisions
- Acts as an optional external agent in the workflow
- Demonstrates extensibility with external services

## Features
- Azure Communication Services integration for email delivery
- Graceful failure handling - workflow continues even if email fails
- Optional agent - workflow works without it being online
- Configurable email templates for different claim outcomes

## Usage
The Communication Agent is automatically called by the orchestrator after claim processing is complete, if the agent is available and online.

## Configuration
Requires Azure Communication Services connection string and sender email configuration.

## Dependencies
- Azure Communication Services Email SDK
- Standard MCP agent framework