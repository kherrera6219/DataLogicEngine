# Privacy Policy

**Effective Date:** January 16, 2026

## 1. Introduction

DataLogicEngine is a local-first knowledge graph workspace for governed AI reasoning. This Privacy Policy explains how the App collects, uses, and discloses information across the current **Local-First Desktop** build and the same Windows application running inside a Windows virtual machine.

## 2. Information We Collect

The App collects the following types of information:

- **Local Identity Information**: Windows account identity metadata used to create the local desktop or Windows VM user profile.
- **Usage Data**: Logs of application usage, including timestamps and feature interactions, for security auditing and performance monitoring.
- **Content Data**: The text queries, documents, and data sources you explicitly upload or input into the App for processing ("User Content").
- **Technical Data**: IP address, device type, and operating system information required for secure connection and session management.

## 3. How We Use Information

We use your information exclusively for the following purposes:

- To provide the core functionality of the App (knowledge synthesis and reasoning).
- To authenticate your local Windows identity.
- To prevent fraud, abuse, and security threats (e.g., adversarial prompt detection).
- To comply with legal obligations and enforce our Terms of Service.

## 4. Deployment Modes & Data residency

The App supports two primary deployment architectures:

### 4.1. Windows VM Mode
In this mode, the same Windows application runs inside a Windows virtual machine.
- **Data Residency**: Application databases remain internal to the installed app stack on the VM.
- **Database Sources**: The App does not use externally hosted PostgreSQL, Redis, Neo4j, ChromaDB, vector, or object-store services as runtime database sources.

### 4.2. Local-First Desktop Mode
In this mode, the App runs as a standalone service on your Windows 11 machine.
- **Data Residency**: Your local data (chat history, profiles, local documents) stays on your machine and is never sent to our servers.
- **Local Identity**: Uses Windows Security Identifier (SID) for zero-config local authentication.

## 5. Cloud Processing & Third Parties

Regardless of deployment mode, to provide advanced reasoning, the App may use cloud-based AI providers.

- **Intelligence Providers**: OpenAI, Anthropic, Google Gemini / Vertex AI, and Microsoft Azure OpenAI, depending on which provider credentials and endpoints you configure.
- **Data Usage**: Prompts, selected context, and provider/model metadata needed to complete the request may be sent to the configured provider. Provider retention, training, regional handling, and logging are governed by the provider account, contract, and API settings you use.
- **Opt-out**: You can disable AI processing or choose a configured provider in `Settings > AI Models`.

## 6. Data Retention

- **Session Data**: Chat history and uploaded data are retained until you explicitly delete them or request account deletion.
- **Audit Logs**: Security logs are retained for 90 days for forensic purposes.

## 7. Your Rights

You have the following rights regarding your data:

- **Access/Export**: You can download a full JSON archive of your data via the `Settings > Privacy` menu.
- **Deletion**: You can request permanent account deletion via the `Settings > Privacy` menu. Upon request, your data will be scheduled for deletion within 30 days.
- **AI Controls**: You can opt out of AI history storage and select your preferred AI provider in `Settings > AI Models`.

## 8. Contact Us

If you have any questions about this Privacy Policy, please contact us at:
privacy@datalogicengine.com
