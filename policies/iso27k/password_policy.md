# Password Policy

| Field | Value |
|---|---|
| **Document ID** | POL-006 |
| **Version** | 1.0 |
| **Status** | Draft |
| **Classification** | Internal |
| **Owner** | IT Manager / CISO |
| **Approved by** | Chief Executive Officer (CEO) |
| **Approval date** | [DD/MM/YYYY] |
| **Next review date** | [DD/MM/YYYY] |
| **Review cycle** | Annual |

---

## 1. Purpose

This policy establishes the requirements for the creation, management, protection, and distribution of passwords used to authenticate access to [Organisation]'s information systems and data. It aligns with modern password security practices — prioritising length and usability alongside multi-factor authentication — in compliance with international cybersecurity standards and applicable regulatory obligations.

Multi-factor authentication (MFA) is strongly encouraged and must be used wherever technically feasible, for both work-related and service accounts.

---

## 2. Scope

This policy applies to:

- All user accounts accessing [Organisation]'s information systems, applications, and services
- All employees, contractors, consultants, and third parties with access to [Organisation] systems
- All systems: on-premises, cloud-hosted, and SaaS applications managed by or on behalf of [Organisation]
- Administrator, privileged, and service accounts

---

## 3. Roles and Responsibilities

### 3.1 IT Manager / System Administrators
- Configure and enforce password settings as defined in this policy on all applicable systems.
- Ensure password management tooling (approved password managers, MFA solutions) is available and maintained.
- Audit password policy compliance at least annually.

### 3.2 CISO
- Own and maintain this policy.
- Review password-related incidents and approve exceptions.

### 3.3 All Users
- Create, maintain, and protect passwords in accordance with this policy.
- Report suspected password compromise immediately to IT.
- Use only organisation-approved password managers.

---

## 4. Password Strength Requirements

All passwords must meet the following minimum strength requirements:

| Account Type | Minimum Length | Complexity |
|---|---|---|
| Standard user accounts | [12] characters | See §4.1 |
| Administrator accounts | [16] characters | See §4.1 |
| Service accounts | [20] characters | See §4.1 |

### 4.1 Complexity Rules
Passwords must contain characters from at least **three** of the following categories:
- Uppercase letters (A–Z)
- Lowercase letters (a–z)
- Digits (0–9)
- Special characters: `! @ # $ % ^ & * ( )` etc.

Additional requirements:
- Very long passwords (e.g., passphrases up to 256 characters) must be supported by all systems.
- Passwords containing the account username, first name, or last name must be rejected.
- Commonly used or known-breached passwords must be rejected where technically feasible (e.g., using a deny list).

### 4.2 Exceptions to Complexity Requirements
A minimum of **4 digits** is acceptable only in the following specific cases:
- PIN used as a **second factor** in addition to a physical token or smart card.
- System not connected to any network and protected by strong physical controls.
- Screen unlock PIN for [Organisation]-managed mobile devices (smartphones, tablets).

---

## 5. Password Change Policy

### 5.1 Change Requirements

| Scenario | Requirement |
|---|---|
| Default or vendor-supplied passwords | Must be changed immediately upon first use |
| Temporary passwords set by IT | Must be changed at first login |
| Suspected or confirmed compromise | Must be changed immediately for all affected systems |
| Periodic change (length-based) | See table below |

#### Periodic Change Schedule (minimum password length-based)

| Minimum password length configured on system | Maximum validity period |
|---|---|
| [12] characters | [12] months |
| [16] characters | [18] months |
| [20+] characters | No mandatory expiry unless compromised |

> Note: NIST SP 800-63B and international security controls framework recommend removing arbitrary periodic password changes in favour of change-on-compromise policies, particularly where MFA is enforced. [Organisation] may align with this guidance on a per-system basis subject to CISO approval.

### 5.2 Additional Change Requirements
- Systems must allow users to change their password at any time.
- Systems must deny reuse of the last **[5]** passwords.
- Shared passwords known to individuals leaving [Organisation] must be changed immediately upon departure.

### 5.3 Exceptions to Periodic Change
Periodic password change is recommended but not mandatory for:
- Service accounts that cannot be used for interactive login.
- PIN codes used as a second factor alongside a physical token.
- Systems not connected to any network with strong physical security controls.
- Screen unlock PINs for [Organisation]-managed mobile devices.

---

## 6. Brute Force Protection

All systems must implement at least one of the following mechanisms to prevent automated brute force attacks:

| Mechanism | Description | Recommended Setting |
|---|---|---|
| **Account lockout** | Disables login for a specific account after repeated failures | Lock for [30] minutes after [5] failed attempts |
| **IP blocklisting** | Blocks source IP addresses after a threshold of failed attempts | Block after [20] attempts from a single IP |
| **Login delay** | Adds incremental delay after each failed attempt | 0.5s → 1s → 2s → 4s progression |

At least one mechanism must be active on all systems accessible from the internet or other untrusted networks.

---

## 7. Password Protection and Handling

- Passwords must never be shared with anyone, including supervisors, colleagues, or IT staff.
- Passwords must never be included in emails, chat messages, tickets, or other electronic communications.
- Passwords must never be communicated verbally over phone or video calls.
- Passwords must be stored only in **[Organisation]-approved password managers**. Storage in plain text, spreadsheets, or browser "remember password" functions is prohibited unless the browser uses an encrypted, organisation-controlled vault.
- Written passwords must be avoided. If necessary (e.g., emergency break-glass credentials), they must be stored in a physically secured location (e.g., sealed envelope in a safe).
- Any user who suspects their password has been compromised must report it immediately to IT and change all affected passwords.

---

## 8. Password Distribution

### 8.1 Distribution via Email
Distributing passwords via email is discouraged. Where unavoidable, the following conditions must all be met:
- No external (non-[Organisation]) email system is involved, or email is encrypted (e.g., Office 365 with transport encryption).
- The password is temporary and forced to change at first use.
- The password expires automatically after **[1 month]** if not used.

### 8.2 Distribution via SMS
SMS is not a secure channel and must not be used to send complete login credentials. SMS may only be used to deliver **partial** authentication information (e.g., an OTP as a second factor) if:
- The message contains only one component of the full credential set (not both username and password).
- The recipient expects the message and is likely to use it promptly.
- The information expires after first use or within **[1 month]** if unused.

---

## 9. Multi-Factor Authentication

- MFA must be enabled on all systems where technically feasible, particularly:
  - Remote access (VPN, remote desktop)
  - Privileged and administrator accounts
  - Cloud services and SaaS applications
  - Systems containing personal data or classified information
- MFA implementation requirements are detailed in the **Access Control Policy (POL-002)**.

---

## 10. Password Managers

- [Organisation] provides an approved password manager for all staff.
- All work-related credentials must be stored in the approved password manager.
- Use of personal, unapproved password managers for work credentials is prohibited.
- The approved password manager must be protected by a strong master password and MFA.

---

## 11. Monitoring and Review

- Password policy configuration compliance is verified on all systems at least **annually**.
- Password-related incidents (compromise, policy violations) are logged and reviewed by the CISO.
- This policy is reviewed annually and updated to reflect current best practices (e.g., NIST SP 800-63B updates).

---

## 12. Exceptions

Exceptions to password requirements require written approval from the CISO, must document the compensating control in place, are time-limited to a maximum of **[6 months]**, and are recorded in the ISMS exception register.

---

## 13. Enforcement

Failure to comply with this policy — including sharing passwords, storing passwords insecurely, or failure to report suspected compromise — constitutes a disciplinary matter and may result in formal disciplinary action up to and including termination.

---

## 14. Related Documents

| Document ID | Title |
|---|---|
| POL-001 | Cybersecurity Policy |
| POL-002 | Access Control Policy |
| POL-008 | Cyber Incident Response Plan |

---

## 15. Definitions

| Term | Definition |
|---|---|
| **MFA** | Multi-Factor Authentication — use of two or more verification factors. |
| **Passphrase** | A password composed of multiple words; typically long and easy to remember. |
| **Service account** | An account used by a system or application, not by a human user interactively. |
| **Break-glass credential** | An emergency-use credential stored securely and used only in exceptional circumstances. |
| **OTP** | One-Time Password — a temporary, single-use code used as a second authentication factor. |
| **Brute force attack** | An automated attempt to guess a password by trying large numbers of combinations. |

---

## 16. Compliance and Regulatory References

- **International Cybersecurity Standards**
- **Security Controls Framework** (Authentication information)
- **NIST SP 800-63B** — Digital Identity Guidelines: Authentication and Lifecycle Management
- **GDPR (EU) 2016/679** — Article 32
- **CyberFundamentals Framework** — Centre for Cybersecurity Belgium

---

## 17. Revision History

| Version | Date | Author | Description of Change |
|---|---|---|---|
| 1.0 | [DD/MM/YYYY] | [Name, Role] | Initial release |

---

## 18. Approval

| Role | Name | Signature | Date |
|---|---|---|---|
| Policy Owner (IT Manager / CISO) | | | |
| Approved by (CEO) | | | |
| Compliance Review | | | |
