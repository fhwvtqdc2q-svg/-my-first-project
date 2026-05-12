# Security Risk Plan

## Transparent assessment

There are real risks if this project depends only on a custom protection layer while stronger third-party security products or attackers exist. This project must not claim that it can fully protect the device or replace Google Play Protect, Apple platform protections, Firebase security, or a professional mobile security solution.

## Main risks

1. Stronger external security tools may detect suspicious behavior if the app requests excessive permissions.
2. App stores may reject the app if privacy claims do not match real behavior.
3. Background operations without consent can be treated as unsafe behavior.
4. SMS or phone-number authentication can increase account takeover risk and privacy exposure.
5. AI features may produce inaccurate security recommendations.
6. Weak backend rules or exposed API keys can allow account or data compromise.
7. Device-level protection is limited by iOS and Android sandboxing. The app cannot safely monitor all apps on the phone.

## Required safety rules

- Do not request permissions that are not required.
- Do not use phone-number authentication or SMS codes.
- Require explicit consent before background operations.
- Require two-factor authentication before sensitive actions.
- Keep AI limited to the user's own account, device settings, connected services, and user-approved data.
- Do not claim that the app monitors all apps or replaces the operating system security model.
- Use Firebase security rules, App Check, HTTPS, encrypted storage, and least-privilege access.
- Keep Google Play Data Safety and Apple App Privacy answers consistent with the privacy policy.

## Recommended architecture

### Authentication

- Email/password with strong password requirements.
- Google Sign-In.
- Apple Sign-In for iOS.
- Passkeys or authenticator-app based two-factor authentication.
- Face ID / Touch ID only as local device unlock, not as stored biometric data.

### Data protection

- Store sensitive local tokens in Keychain on iOS and EncryptedSharedPreferences or Keystore on Android.
- Use Firebase App Check to reduce automated abuse.
- Use Firestore or backend security rules with per-user access only.
- Never store biometric templates.
- Never store phone numbers.

### Background operations

- No hidden background work.
- Notify the user before any background sync or account-impacting action.
- Require two-factor authentication for sensitive background-enabled operations.

### AI features

- Use AI only for explanations, recommendations, and user-approved analysis.
- Do not let AI execute account changes automatically.
- Require user confirmation and two-factor authentication before applying AI-recommended sensitive changes.

## Practical decision

The project should be positioned as a security assistant and account-protection app, not as a full antivirus or full device-monitoring product.
