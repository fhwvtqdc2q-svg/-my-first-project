# AI Features Design

This document defines safe AI features for the project while keeping the security model strict.

## Product position

The AI system is an assistant for the user's own phone, account, connected apps, and security settings. It is not a full antivirus, spyware tool, or hidden monitoring system.

## Allowed AI features

### 1. Security explanation assistant

The AI can explain security status in simple language, including:

- account protection level
- two-factor authentication status
- connected app status
- unusual login explanations
- recommended next steps

### 2. Risk scoring

The AI can calculate a local risk score based on user-approved data:

- weak authentication settings
- missing two-factor authentication
- unknown connected apps
- failed login events
- security alerts
- outdated app configuration

The score must be advisory only. It must not automatically block or change accounts.

### 3. Smart recommendations

The AI may recommend actions such as:

- enable two-factor authentication
- review connected apps
- remove unused sessions
- update password strength
- enable Face ID / Touch ID local unlock
- disable unnecessary permissions

Sensitive recommendations require user confirmation before execution.

### 4. Connected app review

The AI can help the user review apps or services connected to the account. It must only analyze apps that the user added, connected, or approved.

### 5. Background operation review

The AI can warn the user before background work starts. Background work must not begin without explicit consent and two-factor authentication when the action affects account data or security settings.

### 6. Network allowlist assistant

The AI can explain why a domain is allowed or blocked. It can recommend adding a domain, but it must not add domains automatically without user confirmation and two-factor authentication.

### 7. Privacy policy assistant

The AI can explain the privacy policy to the user and answer questions about what data is collected, why it is used, and how deletion requests work.

## Forbidden AI behavior

The AI must not:

- secretly monitor the phone
- read private messages, calls, photos, files, contacts, or passwords without explicit permission and a valid feature need
- access other people's accounts or devices
- use phone numbers or SMS authentication
- perform sensitive actions automatically
- bypass Google, Apple, Firebase, or operating system protections
- claim that it replaces antivirus or platform security
- store biometric data
- expose API keys or tokens to prompts

## Required confirmations

These actions require explicit user approval and two-factor authentication:

- enabling background operations
- changing account security settings
- adding or removing connected services
- changing network allowlist rules
- deleting account data
- exporting account data
- applying AI-recommended sensitive actions

## AI data minimization

The AI should receive the minimum data needed for the requested feature. It should use summaries instead of raw private data whenever possible.

## API key and token isolation

AI provider keys, Google tokens, Apple tokens, Firebase tokens, and backend secrets must stay on a trusted backend or secure platform storage. They must not be placed in frontend code or shown to the AI prompt.

## Audit log

The system should log security decisions without storing private content. Log only:

- event time
- user ID
- feature name
- action requested
- allowed or blocked result
- whether user consent was provided
- whether two-factor authentication was completed

Do not log passwords, phone numbers, private messages, photos, biometric data, API keys, or tokens.

## Implementation phases

### Phase 1

- AI chat for security explanation
- privacy policy explanation
- connected app summary
- risk score preview

### Phase 2

- AI recommendations
- user confirmation screen
- two-factor confirmation for sensitive actions
- audit log

### Phase 3

- network allowlist assistant
- background operation review
- backend proxy for AI API keys
- Firebase App Check and stricter backend rules
