# Privacy Policy

**Effective Date:** January 16, 2026

## 1. Introduction

DataLogic Systems ("we", "our", or "us") operates the DataLogicEngine application ("App"). We are committed to protecting your privacy and ensuring you have full control over your data. This Privacy Policy explains how our App collects, uses, and discloses information across both its **Cloud/Enterprise** and **Local-First Desktop** deployment modes.

## 2. Information We Collect

The App collects the following types of information:

- **Account Information**: Username, email address, and authentication credentials.
- **Usage Data**: Logs of application usage, including timestamps and feature interactions, for security auditing and performance monitoring.
- **Content Data**: The text queries, documents, and data sources you explicitly upload or input into the App for processing ("User Content").
- **Technical Data**: IP address, device type, and operating system information required for secure connection and session management.

## 3. How We Use Information

We use your information exclusively for the following purposes:

- To provide the core functionality of the App (knowledge synthesis and reasoning).
- To authenticate your identity and secure your account.
- To prevent fraud, abuse, and security threats (e.g., adversarial prompt detection).
- To comply with legal obligations and enforce our Terms of Service.

## 4. Deployment Modes & Data residency

The App supports two primary deployment architectures:

### 4.1. Cloud/Enterprise Mode
In this mode, data is stored in secured, tenant-isolated cloud databases.
- **Data Residency**: Data is stored in the region selected by your enterprise administrator.
- **Multi-Tenancy**: Strict logical isolation ensures your data is only accessible to authorized users within your tenant.

### 4.2. Local-First Desktop Mode
In this mode, the App runs as a standalone service on your Windows 11 machine.
- **Data Residency**: Your local data (chat history, profiles, local documents) stays on your machine and is never sent to our servers.
- **Local Identity**: Uses Windows Security Identifier (SID) for zero-config local authentication.

## 5. Cloud Processing & Third Parties

Regardless of deployment mode, to provide advanced reasoning, the App may use cloud-based AI providers.

- **Intelligence Providers**: OpenAI, Microsoft Azure, Anthropic, Google Vertex AI.
- **Data Usage**: Only the specific prompt or query you are currently processing is sent ephemerally to these providers. We have entered into enterprise agreements ensuring **your data is NOT used to train their public models** and is not retained by them beyond the processing window.
- **Opt-out**: You can choose which providers to use or disable cloud reasoning entirely in `Settings > AI Controls`.

## 6. Data Retention

- **Session Data**: Chat history and uploaded data are retained until you explicitly delete them or request account deletion.
- **Audit Logs**: Security logs are retained for 90 days for forensic purposes.

## 7. Your Rights

You have the following rights regarding your data:

- **Access/Export**: You can download a full JSON archive of your data via the `Settings > Privacy` menu.
- **Deletion**: You can request permanent account deletion via the `Settings > Privacy` menu. Upon request, your data will be scheduled for deletion within 30 days.
- **AI Controls**: You can opt-out of AI history storage and select your preferred AI provider in `Settings > AI Controls`.

## 8. Contact Us

If you have any questions about this Privacy Policy, please contact us at:
privacy@datalogicengine.com
