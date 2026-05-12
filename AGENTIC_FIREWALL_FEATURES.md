# Agentic Firewall Features

This project adds a safe design inspired by GitHub's Agentic Workflow Firewall concept.

## Purpose

The goal is to protect AI-assisted workflows by restricting outbound network access, reducing data leakage, and keeping API credentials away from the AI agent process.

## Core features to implement

### 1. Domain allowlist

AI or automation features must only connect to explicitly approved domains.

Default allowed domains:

- github.com
- api.github.com
- raw.githubusercontent.com
- firebase.googleapis.com
- identitytoolkit.googleapis.com
- securetoken.googleapis.com
- googleapis.com
- appleid.apple.com

All other outbound HTTP/HTTPS traffic should be blocked by default.

### 2. User consent before background operations

No background network operation should run without explicit user consent.
Sensitive background operations must require two-factor authentication before execution.

### 3. No phone-number authentication

The firewall and authentication system must not use phone numbers or SMS codes.
Use email, passkeys, authenticator apps, Google Sign-In, Apple Sign-In, Face ID / Touch ID local unlock, or device confirmation.

### 4. API key isolation

API keys must not be exposed directly to AI prompts, browser UI, or untrusted app code.
Use a backend proxy or sidecar-like service to hold secrets and forward only approved requests.

### 5. Audit logs

Record safe audit logs for security events:

- requested domain
- request time
- allow or block decision
- user ID
- feature that triggered the request
- whether two-factor authentication was required

Do not log passwords, tokens, phone numbers, private messages, photos, files, or biometric data.

### 6. AI execution limits

AI may recommend actions, but it must not automatically perform sensitive changes.
Sensitive actions require user confirmation and two-factor authentication.

## Safe product positioning

This project should be presented as:

- AI Security Assistant
- Account Protection Tool
- Connected Apps Manager
- Network Permission Guard

It must not be described as a full antivirus, spyware detector, or full-device monitoring tool.

## Store compliance note

Google Play Data Safety and Apple App Privacy answers must match the privacy policy. Do not claim no data is collected if Firebase, Google Sign-In, analytics, or account security features are used.
