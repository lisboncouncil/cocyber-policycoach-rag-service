# Backup and Recovery Policy

| Field | Value |
|---|---|
| **Document ID** | POL-004 |
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

This policy establishes the requirements for protecting [Organisation]'s critical information and systems against data loss through a structured backup and recovery programme. It ensures that data and systems can be restored to an operational state within defined timeframes following any disaster scenario, including system failure, accidental deletion, fire, or malware outbreak. This policy supports compliance with international cybersecurity standards and applicable regulatory obligations.

[Organisation] is committed to continually reviewing and improving its backup and recovery capabilities in line with evolving business needs and threat landscape.

---

## 2. Scope

This policy applies to:

- All critical and confidential information systems and data owned or operated by [Organisation]
- All backup media, storage locations, and cloud environments used for backup purposes
- All personnel responsible for operating, monitoring, or managing backup and recovery processes
- Third-party and cloud-hosted systems where [Organisation] holds contractual responsibility for data protection

Backup is not required where data loss is acceptable or where equivalent recovery measures (e.g., static configurations easily redeployed) are in place, provided this is formally documented and approved by the asset owner.

---

## 3. Roles and Responsibilities

### 3.1 Asset Owner
- Define recovery objectives (RPO and RTO) for assigned critical systems.
- Ensure an appropriate backup and recovery procedure exists for each owned system.
- Accept formal responsibility for the adequacy of backup coverage.

### 3.2 IT Manager / System Administrators
- Implement, operate, and monitor backup processes.
- Ensure backup jobs complete successfully and investigate failures.
- Execute recovery tests at least annually.
- Document all backup and recovery activities.

### 3.3 CISO
- Review backup policy compliance during annual internal audits.
- Escalate unresolved backup failures or significant RPO/RTO gaps to executive leadership.

### 3.4 All Employees
- Ensure work files are stored in designated, backed-up locations.
- Report suspected data loss incidents immediately to IT.

---

## 4. Backup Requirements

### 4.1 Coverage
A documented backup and recovery procedure must exist for all critical systems. The procedure must define:

- What is backed up (systems and data)
- How backups are performed
- Backup monitoring process
- Backup frequency and schedule
- Retention period
- Storage location(s)
- Data transfer method and encryption

### 4.2 Recovery Objectives (RPO and RTO)
Backup procedures must meet business-defined recovery objectives based on risk assessment and information classification:

| System Criticality | Minimum RPO | Minimum RTO |
|---|---|---|
| Critical / High | [e.g., 4 hours] | [e.g., 4 hours] |
| Important / Medium | [e.g., 24 hours] | [e.g., 24 hours] |
| Standard / Low | [e.g., 7 days] | [e.g., 72 hours] |

These values must be formally agreed with asset owners and reviewed annually.

### 4.3 Backup Schedule
[Organisation] uses the **Grandfather-Father-Son (GFS) scheme** (see Annex A) as the standard rotation model for environments with large data volumes or where version history is required.

### 4.4 Encryption
Backup data must be encrypted when:
- Transmitted over a network (including backup replication traffic)
- Stored on media that could be accessed by unauthorised persons
- Stored or transported off-site

The encryption key required to decrypt off-site media must not be stored exclusively on-site.

### 4.5 Offsite Storage (3-2-1 Strategy)
To prevent simultaneous loss of primary data and backups, [Organisation] applies the **3-2-1 backup strategy** (see Annex B):

- **3** copies of data (1 primary + 2 backups)
- **2** different storage media types
- **1** copy stored off-site or in a geographically separate location

An up-to-date register of all off-site media must be maintained.

### 4.6 Backup Monitoring
All backup jobs must be monitored to ensure successful completion. Evidence of successful backup (logs, reports, or automated alerts) must be available on demand.

---

## 5. Recovery Testing

- Recovery tests must be performed for all backup methods used for critical systems **at least once per year**.
- An unplanned operational restore may count as a recovery test if documented.
- Test results must be documented, including: date, system tested, data recovered, RTO achieved, and any issues identified.
- Identified gaps must be remediated within a defined timeframe agreed with the asset owner.

---

## 6. Monitoring and Review

- Backup logs must be reviewed by IT at least [weekly].
- Failed backups must be investigated and resolved within [1 business day].
- Backup coverage and retention settings must be reviewed at least **annually** or upon any significant infrastructure change.
- Policy effectiveness is assessed during annual ISMS management review.

---

## 7. Exceptions

Exceptions to backup requirements (e.g., systems excluded from backup due to static configuration) must be:
- Formally documented with a business justification and asset owner approval.
- Approved by the CISO.
- Recorded in the ISMS exception register with an expiry date.

---

## 8. Enforcement

Failure to implement or maintain backup procedures for critical systems — or failure to report backup failures — will be treated as a disciplinary matter. Wilful circumvention of backup controls may result in formal disciplinary action up to and including termination.

---

## 9. Related Documents

| Document ID | Title |
|---|---|
| POL-001 | Cybersecurity Policy |
| POL-003 | Asset Management Policy |
| POL-007 | Vulnerability and Patch Management Policy |
| POL-008 | Cyber Incident Response Plan |
| Annex A | GFS Backup Schedule |
| Annex B | 3-2-1 Backup Strategy |

---

## 10. Definitions

| Term | Definition |
|---|---|
| **RPO** | Recovery Point Objective — the maximum acceptable period of data loss following a disruption. |
| **RTO** | Recovery Time Objective — the maximum acceptable time to restore a system after a disruption. |
| **GFS** | Grandfather-Father-Son — a backup rotation scheme combining daily, weekly, and monthly backups. |
| **3-2-1 Strategy** | A backup approach requiring 3 copies on 2 media types with 1 off-site. |
| **Full backup** | A complete copy of the entire dataset. |
| **Incremental backup** | A copy of data changed since the last incremental backup. |
| **Differential backup** | A copy of data changed since the last full backup. |

---

## 11. Compliance and Regulatory References

- **International Cybersecurity Standards**
- **Security Controls Framework** (Information backup)
- **GDPR (EU) 2016/679** — Article 32 (integrity and availability of processing systems)
- **CIS Controls v8** — Control 11 (Data Recovery)
- **CyberFundamentals Framework** — Centre for Cybersecurity Belgium

---

## 12. Revision History

| Version | Date | Author | Description of Change |
|---|---|---|---|
| 1.0 | [DD/MM/YYYY] | [Name, Role] | Initial release |

---

## 13. Approval

| Role | Name | Signature | Date |
|---|---|---|---|
| Policy Owner (IT Manager / CISO) | | | |
| Approved by (CEO) | | | |
| Compliance Review | | | |

---

## Annex A — Grandfather-Father-Son (GFS) Backup Schedule

The GFS scheme combines daily, weekly, and monthly backups to balance storage efficiency with version history depth.

| Level | Frequency | Retention | Description |
|---|---|---|---|
| **Son (daily)** | Daily (Mon–Thu) | 3 weeks rolling | Incremental or differential backup |
| **Father (weekly)** | Weekly (Friday) | 1 month rolling | Full backup |
| **Grandfather (monthly)** | Last business day of month | [Quarterly / Annual] | Full backup stored off-site |

### Backup Types Reference

| Type | Description |
|---|---|
| **Full** | Complete copy of all data. Slow and storage-intensive; required as the base for incremental/differential chains. |
| **Incremental** | Only data changed since the last incremental backup. Fast and space-efficient; requires the full chain to restore. |
| **Differential** | Only data changed since the last full backup. Larger than incremental but faster to restore. |

---

## Annex B — 3-2-1 Backup Strategy

The 3-2-1 strategy ensures there is no single point of failure for data:

| Rule | Requirement |
|---|---|
| **3 copies** | 1 primary (production) + 2 backup copies |
| **2 media types** | e.g., NAS + tape, NAS + cloud, internal HDD + external HDD |
| **1 off-site location** | At least one copy stored in a geographically separate location (physical or cloud) |

### Recovery Procedure

1. If production data is lost: restore from the on-site backup copy.
2. If the on-site backup is unavailable or corrupt: retrieve the off-site copy.
3. Once data is restored: restart the 3-2-1 backup cycle immediately.
4. Document the incident and corrective actions in the ISMS incident register.
