# Access Control Policy

| Field | Value |
|---|---|
| **Document ID** | POL-002 |
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

This policy establishes the framework for managing access to [Organisation]'s information systems, applications, and data assets. It ensures that access is granted on the basis of business need, using the principle of least privilege, and that all access is authenticated, authorised, and periodically reviewed. This policy supports compliance with international cybersecurity standards and applicable regulatory obligations.

---

## 2. Scope

This policy applies to:

- All information systems, applications, and data assets owned or managed by [Organisation]
- All user accounts: employees, contractors, consultants, third parties, and service accounts
- All access methods: on-premises, remote, cloud-based, and machine-to-machine
- All devices used to access [Organisation] systems, whether managed or unmanaged

---

## 3. Roles and Responsibilities

### 3.1 IT Manager / CISO
- Own and maintain this policy
- Oversee the implementation of access controls across all systems
- Approve access requests for privileged accounts
- Ensure periodic access reviews are conducted

### 3.2 HR Department
- Notify IT of all new starters, leavers, and role changes in a timely manner
- Initiate access provisioning and de-provisioning requests using the defined forms

### 3.3 Department Managers (N+1)
- Approve access requests for personnel within their area
- Confirm access rights remain appropriate at each periodic review
- Immediately notify IT of any role changes or departures

### 3.4 IT Operations / System Administrators
- Provision, modify, and revoke accounts in accordance with approved requests
- Monitor authentication events and report anomalies
- Maintain audit logs of all access management actions

### 3.5 All Users
- Use only accounts and access rights assigned to them
- Report suspected unauthorised access or account compromise immediately
- Comply with the Password Policy (POL-006)

---

## 4. Policy Requirements

### 4.1 Principle of Least Privilege
Every user — internal or external — is granted the minimum access required to perform their function. Access rights are role-based wherever technically feasible.

### 4.2 User Account Management

#### 4.2.1 Standard User Accounts
- Accounts must be unique and personal; shared accounts are prohibited except where technically unavoidable (see §4.2.4).
- Accounts must be password-protected in accordance with the **Password Policy (POL-006)**.
- New accounts may only be requested by an authorised person (HR or N+1) using the **Account Creation and Modification Form (ACMF — Annex A)**.
- Accounts must be suspended or removed when no longer required (e.g., upon termination of contract, role change, or extended absence).

#### 4.2.2 Privileged Accounts
- Privileged accounts (e.g., domain administrator, root, superuser) must be restricted to the minimum number of users necessary.
- Privileged accounts must not be used for day-to-day activities. Owners must use a separate non-privileged account for routine tasks.
- Account names must not reveal privileged status.
- Multi-factor authentication (MFA) is mandatory for all privileged accounts, particularly those accessible over the internet.

#### 4.2.3 Accounts for External Staff and Third Parties
- External accounts must be easily identifiable (e.g., via a naming prefix or description).
- External accounts must expire automatically every [3 months] unless formally renewed.
- Access must be revoked immediately upon contract termination.

#### 4.2.4 Shared Accounts
- Shared accounts must be avoided. Where technically unavoidable, the following controls must be in place:
  - A documented list of individuals authorised to use the account.
  - A controlled process for password changes, including upon departure of any authorised user.
  - Abuse prevention measures.

#### 4.2.5 Service and Machine-to-Machine Accounts
- Service accounts must be identifiable (e.g., via a naming prefix).
- The principle of least privilege applies.
- Interactive use of service accounts must be prevented where technically feasible.

### 4.3 Authentication

- All connection attempts (successful and failed) must be logged and monitored by the IT Manager.
- Initial/temporary passwords must be securely transmitted directly to the user and forced to change at first login.
- MFA must be enforced where technically feasible, particularly for remote access and privileged accounts.
- Accounts must be suspended for a defined period (e.g., [30 minutes]) after [3] failed authentication attempts within [5 minutes].
- Accounts must be suspended automatically after [90] days of inactivity.

### 4.4 Authorisation

- Access grants, modifications, and revocations must be formally requested using the ACMF or Account Removal Form (ARF — Annex B).
- Requests may only be initiated by HR or the N+1 of the affected user.
- Formal approval by the designated [IT / CISO / Department Head] is required before access is granted.
- Authorisation groups and role-based access control (RBAC) must be used wherever possible.

### 4.5 Remote Access

- Remote access to critical and confidential systems from untrusted networks must be restricted to authorised users.
- All remote access must be established through a VPN or equivalent encrypted channel.
- MFA must be enforced for all remote access sessions.

### 4.6 Access Reviews

- Access rights for all users must be reviewed at least every [6 months] or upon any role change.
- Reviews are initiated by IT and confirmed by Department Managers.
- Accounts with excessive or no-longer-required rights must be modified or revoked within [5 business days] of review completion.

---

## 5. Monitoring and Logging

- All authentication events (successful and failed) on critical and confidential systems must be logged.
- Logs must be retained for a minimum of [12 months] and protected against unauthorised modification.
- The IT Manager must review access logs for anomalies at least [monthly].

---

## 6. Exceptions

Exceptions to this policy (e.g., shared accounts, bypass of MFA) may be granted only with the written approval of the CISO. Exceptions must:
- Document the business justification and proposed compensating control.
- Be time-limited (maximum 6 months) and recorded in the ISMS exception register.
- Be reviewed at expiry for renewal or revocation.

---

## 7. Enforcement

Non-compliance with this policy will be handled in accordance with [Organisation]'s disciplinary procedures. Violations may result in suspension of access rights, formal disciplinary action, or, in cases of intentional misuse, termination of employment or contract and referral to law enforcement.

---

## 8. Related Documents

| Document ID | Title |
|---|---|
| POL-001 | Cybersecurity Policy |
| POL-006 | Password Policy |
| POL-008 | Cyber Incident Response Plan |
| Annex A | Account Creation and Modification Form (ACMF) |
| Annex B | Account Removal Form (ARF) |

---

## 9. Definitions

| Term | Definition |
|---|---|
| **Least privilege** | The practice of granting only the minimum access rights necessary to perform a function. |
| **MFA** | Multi-Factor Authentication — use of two or more verification factors to authenticate a user. |
| **RBAC** | Role-Based Access Control — access rights assigned based on a user's role within the organisation. |
| **Privileged account** | An account with elevated permissions, such as administrator or root access. |
| **Service account** | An account used by a system or application for machine-to-machine communication. |
| **VPN** | Virtual Private Network — an encrypted tunnel for secure remote access. |

---

## 10. Compliance and Regulatory References

- **International Cybersecurity Standards** 5.16, 5.17, 5.18, 8.2
- **Security Controls Framework**
- **GDPR (EU) 2016/679** — Article 32 (technical and organisational measures)
- **CyberFundamentals Framework** — Centre for Cybersecurity Belgium

---

## 11. Revision History

| Version | Date | Author | Description of Change |
|---|---|---|---|
| 1.0 | [DD/MM/YYYY] | [Name, Role] | Initial release |

---

## 12. Approval

| Role | Name | Signature | Date |
|---|---|---|---|
| Policy Owner (IT Manager / CISO) | | | |
| Approved by (CEO) | | | |
| Compliance Review | | | |

---

## Annex A — Account Creation and Modification Form (ACMF)

**Classification: INTERNAL**

| Field | Details |
|---|---|
| **Request type** | New account / Modification |
| **User full name** | |
| **Department** | |
| **Job title / Role** | |
| **Start date** | |
| **Systems / Applications requiring access** | |
| **Access level / Role required** | |
| **Requested by (N+1 or HR)** | |
| **Approved by** | |
| **Approval date** | |
| **IT action completed by** | |
| **Date completed** | |

---

## Annex B — Account Removal Form (ARF)

**Classification: INTERNAL**

| Field | Details |
|---|---|
| **User full name** | |
| **Department** | |
| **Last working day** | |
| **Systems / Applications to revoke** | |
| **Reason for removal** | Resignation / Termination / Contract end / Other |
| **Requested by (N+1 or HR)** | |
| **Approved by** | |
| **Approval date** | |
| **IT action completed by** | |
| **Date completed** | |
| **Confirmation: all access revoked** | Yes / No |
