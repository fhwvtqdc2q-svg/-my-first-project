# Apple Intelligence, Voice Preview, Face ID, and Two-Factor Authentication Specification

## Purpose

This specification defines how the project should support Apple Intelligence-style assistance, voice preview, verbal confirmation, Face ID, and two-factor authentication in a safe and store-compliant way.

The system must be designed for the user's own device and account only. It must not access other people’s accounts, phone numbers, SMS messages, private messages, calls, photos, files, contacts, passwords, or background activity without explicit user consent and two-factor authentication when required.

## Apple Intelligence-style assistant

If Apple Intelligence APIs, system writing tools, Siri/App Intents, or on-device AI features are available, the app may use them only for:

- explaining security status
- summarizing privacy and security settings
- previewing recommendations
- helping the user understand connected apps
- preparing user-approved actions
- generating a spoken-style confirmation before sensitive actions

The assistant must not perform sensitive changes automatically.

## Voice preview before activation

Before any sensitive AI action is enabled, the app must present a voice preview or spoken-style confirmation message.

Required Arabic confirmation:

"سأفعّل ميزة الذكاء الاصطناعي فقط على هاتفك وحسابك الشخصي. لن أستخدم رقم الهاتف أو رسائل SMS. لن أعمل في الخلفية أو أغيّر إعدادات الأمان أو أصل إلى بيانات خاصة بدون موافقتك الصريحة والمصادقة الثنائية. هل توافق على تفعيل هذه الميزة؟"

Required English confirmation:

"I will enable AI features only for your own phone and account. I will not use phone numbers or SMS. I will not run in the background, change security settings, or access private data without your explicit consent and two-factor authentication. Do you approve enabling this feature?"

## Activation flow

The activation flow must be:

1. Show a clear explanation of the AI feature.
2. Play or display the voice preview confirmation.
3. Ask for explicit approval.
4. Require Face ID / Touch ID for local device confirmation.
5. Require two-factor authentication for high-risk actions.
6. Log only a safe audit event, without private content.
7. Enable the feature only after all required confirmations pass.

## Face ID / Touch ID

Face ID or Touch ID may be used only for local device authentication and secure unlock.

The app must not collect, store, transmit, or directly access biometric data. Biometric verification is handled by the operating system. The app only receives success or failure.

## Two-factor authentication

Two-factor authentication is required for:

- enabling AI actions that affect account security
- enabling background processing
- changing authentication settings
- adding or removing connected apps/services
- deleting or exporting account data
- adding or removing network allowlist domains
- applying AI-recommended sensitive changes

Phone number and SMS-based verification are not allowed. Use email confirmation, authenticator apps, passkeys, hardware/device confirmation, or trusted-device confirmation.

## Voice approval rules

The user must give explicit approval. Valid examples:

- "أوافق"
- "نعم، فعّل الميزة"
- "تأكيد"
- "I approve"
- "Yes, enable it"
- "Confirm"

Silence, unclear speech, or ambiguous answers must not be treated as consent.

## Forbidden behavior

The app and AI assistant must not:

- activate AI silently
- use phone numbers or SMS
- bypass Face ID or two-factor authentication
- perform hidden background work
- claim full device monitoring or antivirus replacement
- store biometric data
- expose tokens or API keys to AI prompts
- perform sensitive account actions without explicit approval

## Recommended iOS implementation notes

Use Apple platform APIs appropriately:

- LocalAuthentication for Face ID / Touch ID
- App Intents or Shortcuts for user-approved voice-driven actions
- AVSpeechSynthesizer for local voice preview when appropriate
- Keychain for sensitive local tokens
- Secure Enclave / passkeys where available
- BackgroundTasks only for declared, user-approved, non-secret background work

## Audit logging

Log only security metadata:

- timestamp
- user ID
- feature name
- action requested
- consent result
- biometric authentication result
- two-factor authentication result
- allowed or blocked decision

Do not log private content, passwords, phone numbers, SMS, biometric data, tokens, or API keys.
