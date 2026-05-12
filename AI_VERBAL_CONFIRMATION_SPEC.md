# AI Verbal Confirmation Specification

This document adds a verbal confirmation layer for AI-powered security actions.

## Purpose

Before the AI performs or recommends any sensitive action, the application must clearly confirm the action verbally or through a spoken-style confirmation message. The goal is to make sure the user understands what will happen before approval.

## Required confirmation sentence

For sensitive actions, the AI must say or display a clear confirmation like:

"I will only perform this action on your own phone and your own account. I will not access other people's accounts, phone numbers, SMS messages, private messages, calls, photos, files, contacts, passwords, or background activity without your explicit consent and two-factor authentication. Do you approve this action?"

Arabic version:

"سأقوم بهذا الإجراء فقط على هاتفك وحسابك الشخصي. لن أصل إلى حسابات الآخرين، أو أرقام الهواتف، أو رسائل SMS، أو الرسائل الخاصة، أو المكالمات، أو الصور، أو الملفات، أو جهات الاتصال، أو كلمات المرور، أو أي نشاط بالخلفية بدون موافقتك الصريحة والمصادقة الثنائية. هل توافق على تنفيذ هذا الإجراء؟"

## Actions that require verbal confirmation

The AI must ask for verbal or spoken-style confirmation before:

- enabling background operations
- changing security settings
- applying AI security recommendations
- connecting or removing apps/services
- adding or removing allowed domains
- exporting user data
- deleting user data
- changing authentication settings
- reviewing connected services
- starting any action that affects account state

## Confirmation requirements

The confirmation must include:

1. What action will happen.
2. Which account or device it applies to.
3. What data may be used.
4. Whether background operation is involved.
5. Whether two-factor authentication is required.
6. A clear user approval question.

## User approval format

The application should accept approval only when the user gives an explicit response such as:

- "I approve"
- "Yes, continue"
- "Confirm"
- "أوافق"
- "نعم، تابع"
- "تأكيد"

Ambiguous responses must not approve sensitive actions.

## Two-factor authentication requirement

After the verbal confirmation, sensitive actions must still require two-factor authentication. Verbal confirmation alone is not enough for high-risk actions.

## Forbidden behavior

The AI must not:

- assume consent from silence
- perform sensitive actions automatically
- use phone numbers or SMS for verification
- hide background activity
- summarize risk without explaining important limitations
- claim full device control or antivirus-level protection

## Safe behavior

The AI should say clearly when it cannot perform an action safely or when an action is outside the allowed security model.

Example:

"I cannot perform this action automatically because it affects account security. Please confirm the action and complete two-factor authentication."
