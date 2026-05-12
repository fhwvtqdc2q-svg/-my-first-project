# AI Security Assistant

This project is designed as a privacy-first AI Security Assistant for the user's own account, phone, connected apps, and security settings.

## What is ready

The repository now contains the essential product, privacy, security, AI, and platform specifications needed before building the actual iOS and Android apps.

## Core principles

- AI works only for the user's own phone and account.
- No phone number or SMS authentication.
- No hidden background operations.
- Sensitive actions require explicit approval, Face ID / Touch ID when available, and two-factor authentication.
- AI must verbally confirm sensitive actions before activation.
- Biometric data is never collected, stored, transmitted, or directly accessed.
- API keys and tokens must be isolated from AI prompts and frontend code.
- The product is an AI Security Assistant, not a full antivirus or full-device monitoring tool.

## Main documents

- `privacy_policy.md` — Privacy policy for Google Play and Apple App Store.
- `RegistrationUI.html` — Secure registration interface without phone number use.
- `SecurityWidget.swift` — SwiftUI widget example for account security status.
- `SECURITY_RISK_PLAN.md` — Transparent risk and security positioning plan.
- `AGENTIC_FIREWALL_FEATURES.md` — Agentic firewall-inspired allowlist and network safety design.
- `AI_FEATURES_DESIGN.md` — Safe AI feature design.
- `AI_VERBAL_CONFIRMATION_SPEC.md` — Verbal confirmation rules before sensitive AI actions.
- `APPLE_INTELLIGENCE_VOICE_AUTH_SPEC.md` — Apple Intelligence-style voice preview, Face ID, and two-factor authentication design.

## Recommended build order

1. Firebase Authentication without phone/SMS provider.
2. Google Sign-In.
3. Apple Sign-In for iOS.
4. Face ID / Touch ID using LocalAuthentication on iOS.
5. Two-factor authentication using email, authenticator app, passkeys, or trusted device confirmation.
6. AI assistant backend or safe on-device AI flow.
7. Verbal confirmation before sensitive actions.
8. Audit logs without private content.
9. Network allowlist / firewall-style guard for AI actions.
10. Google Play Data Safety and Apple App Privacy forms.

## Privacy policy URL

Raw privacy policy URL:

https://raw.githubusercontent.com/fhwvtqdc2q-svg/-my-first-project/main/privacy_policy.md

Use this URL in Google Play Console and App Store Connect until a better hosted webpage is created.

## Not ready yet

This repository is ready at the design and documentation level. It is not yet a complete production app. The next step is building the actual iOS app, Android app, Firebase backend, and AI backend.
