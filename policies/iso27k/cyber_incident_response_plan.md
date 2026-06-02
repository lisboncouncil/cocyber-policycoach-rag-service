# Cyber Incident Response Plan

| Field | Value |
|---|---|
| **Document ID** | POL-008 |
| **Version** | 1.0 |
| **Status** | Draft |
| **Classification** | Internal — Restricted |
| **Owner** | CISO |
| **Approved by** | Chief Executive Officer (CEO) |
| **Approval date** | [DD/MM/YYYY] |
| **Next review date** | [DD/MM/YYYY] |
| **Review cycle** | Annual (and after any significant incident) |

---

## 1. Purpose and Objectives

This Cyber Incident Response Plan (CIRP) establishes [Organisation]'s structured approach to detecting, containing, eradicating, and recovering from cyber incidents. It supports a rapid and effective response aligned with [Organisation]'s security and business objectives.

### 1.1 Objectives

- Provide clear guidance on the steps required to respond to cyber incidents.
- Define the roles, responsibilities, and authority of personnel involved in incident management.
- Outline internal and external communication processes during incident response.
- Ensure compliance with applicable legal and regulatory notification obligations.
- Support continual improvement through structured post-incident review.

### 1.2 Commitment to Improvement
[Organisation] is committed to reviewing and improving this plan following each significant incident and at least annually, as part of the ISMS continual improvement cycle.

---

## 2. Scope

This plan applies to:

- All cyber incidents affecting [Organisation]'s information systems, data, personnel, or third-party providers.
- All employees, contractors, and third parties who detect, report, or respond to cyber incidents.
- All environments: on-premises, cloud-hosted, and remote/home office.

---

## 3. Standards and Frameworks

This plan was developed in reference to the following standards (latest editions apply):

- International incident management best practices
- International Cybersecurity Standards 5.25, 5.26, 5.27, 5.28
- NIST SP 800-61 — Computer Security Incident Handling Guide
- CyberFundamentals Framework (www.cyfun.be)
- Australian Cyber Security Centre — Cyber Incident Response Plan

---

## 4. Definitions and Terminology

| Term | Definition |
|---|---|
| **Threat** | A potential cause of an unwanted event that may harm systems or data. |
| **Vulnerability** | A weakness in a system that could be exploited by a threat. |
| **Event** | Any observable occurrence in a system or network. |
| **Alert** | A notification indicating that a suspicious event has occurred. |
| **Incident** | A confirmed event that compromises the confidentiality, integrity, or availability of information. |
| **CIRT** | Cyber Incident Response Team — the operational team managing incident response. |
| **MT** | Management Team — the strategic team providing oversight for significant incidents. |

---

## 5. Common Threat Vectors

| Vector | Examples |
|---|---|
| External / Remote | Phishing, brute force, exploitation of public-facing vulnerabilities |
| Web application | SQL injection, XSS, API abuse |
| Supply chain | Compromised third-party software or services |
| Insider | Malicious or negligent employee or contractor |
| Physical | Theft of device, unauthorised access to premises |
| Removable media | Infected USB drives |

---

## 6. Common Incident Types and Initial Response

| Incident Type | Initial Response |
|---|---|
| **Ransomware** | Isolate affected systems; do not pay ransom without CISO/CEO approval; notify CIRT |
| **Data breach** | Identify scope; preserve evidence; assess notification obligations; notify CIRT |
| **DDoS attack** | Engage ISP/DDoS mitigation service; monitor impact on critical systems |
| **Malware infection** | Isolate affected endpoint; run forensic scan; assess lateral movement |
| **Phishing campaign** | Block sender; identify recipients; reset credentials if clicked; awareness alert |
| **Unauthorised access** | Revoke compromised credentials; preserve logs; assess data accessed |
| **Lost or stolen device** | Remote wipe if possible; revoke device access; assess data at risk |
| **Insider threat** | Preserve evidence; escalate to HR and CISO; restrict access as appropriate |

---

## 7. Incident Response Process

### Phase 1 — Preparation
- All CIRT members are trained and familiar with their responsibilities.
- Contact lists, playbooks, and communication templates are maintained and accessible offline.
- The CIRP is tested at least **annually** through tabletop exercises or simulations.

### Phase 2 — Detection and Reporting
- Any employee, contractor, or automated system that detects a suspected incident must report it immediately to the primary contact point (see Section 8).
- The IT Manager / CIRT assesses whether the event constitutes a security incident.
- Incidents are logged in the **ISMS incident register** from the moment of detection.

### Phase 3 — Classification and Triage

| Severity | Criteria | Response SLA |
|---|---|---|
| **Critical** | Active breach, data exfiltration, ransomware, service outage | Immediate (< 1 hour) |
| **High** | Confirmed compromise, significant data at risk | < 4 hours |
| **Medium** | Suspected compromise, limited scope | < 24 hours |
| **Low** | Minimal impact, no confirmed breach | < 72 hours |

### Phase 4 — Containment
- **Short-term:** Isolate affected systems, block malicious traffic, revoke compromised credentials.
- **Long-term:** Apply patches, reconfigure controls, restore from clean backups.
- Containment decisions are made by the CIRT and documented.

### Phase 5 — Eradication
- Identify and remove the root cause (malware, unauthorised accounts, misconfiguration).
- Verify that all affected systems are clean before restoration.

### Phase 6 — Recovery
- Restore systems from verified clean backups in accordance with the **Backup and Recovery Policy (POL-004)**.
- Monitor restored systems closely for recurrence.
- Confirm systems are fully operational before returning to production.

### Phase 7 — Post-Incident Review
- A post-incident review must be conducted within **[5 business days]** of incident closure for Critical/High incidents and within **[15 business days]** for Medium/Low incidents.
- The review documents: root cause, timeline, effectiveness of response, lessons learned, and recommended improvements.
- Findings are reported to CISO and, for significant incidents, to executive leadership.
- Action items from the review are tracked to completion.

---

## 8. Roles and Responsibilities

### 8.1 Cyber Incident Response Team (CIRT)

The CIRT manages the operational response to cyber incidents.

| Role | Name | Primary Contact | Backup Contact |
|---|---|---|---|
| CIRT Lead (CISO) | [Name] | [Phone / Email] | [Name / Contact] |
| IT Security | [Name] | [Phone / Email] | [Name / Contact] |
| IT Operations | [Name] | [Phone / Email] | [Name / Contact] |
| Legal / Compliance | [Name] | [Phone / Email] | [Name / Contact] |
| External IR Provider | [Vendor name] | [Phone / Email] | [Name / Contact] |

For significant incidents, the CIRT may be expanded to include additional technical or business stakeholders.

### 8.2 Management Team (MT)

For significant incidents, the MT provides strategic oversight and direction:

| Role | Name | Primary Contact |
|---|---|---|
| CEO | [Name] | [Phone / Email] |
| CFO | [Name] | [Phone / Email] |
| Legal Counsel | [Name] | [Phone / Email] |
| Communications / PR | [Name] | [Phone / Email] |

MT responsibilities:
- Manage strategic decisions and escalations.
- Approve communication to external stakeholders, regulators, and media.
- Authorise emergency expenditure (e.g., external forensics, legal counsel).

---

## 9. Reporting Contacts

### 9.1 Internal Reporting (24/7)
| Channel | Contact |
|---|---|
| Primary (business hours) | [CIRT Lead: name, phone, email] |
| Secondary / Out of hours | [Backup contact: name, phone] |
| Emergency escalation | [CEO / senior management: phone] |

### 9.2 External Reporting Obligations

| Recipient | Trigger | Deadline |
|---|---|---|
| **Data Protection Authority** (e.g., national DPA) | Personal data breach under GDPR | 72 hours from awareness |
| **National CSIRT / CERT** | Significant incident (NIS2) | As per NIS2 national implementation |
| **Sector regulator** | Sector-specific obligation | As defined by regulator |
| **Law enforcement** | Criminal activity suspected | Without undue delay |
| **Affected individuals** | High-risk personal data breach | Without undue delay |
| **Cyber insurance provider** | As per policy terms | Per contract |

---

## 10. Communications

### 10.1 Principles
- Communicate on a **need-to-know basis**.
- Avoid speculation; communicate only confirmed facts.
- Use secure out-of-band communication channels if primary systems are compromised.
- Designate a single spokesperson for all external communications.

### 10.2 Stakeholder Communication Matrix

| Stakeholder | Communication Channel | Frequency during Incident |
|---|---|---|
| Internal staff | Email / internal messaging | As needed; major updates at each phase |
| Affected managers | Direct call / email | Immediately upon scope determination |
| Customers / clients | Email / official statement | Upon confirmed impact; per legal requirement |
| Suppliers / partners | Direct contact | If supply chain affected |
| Media | Press statement via PR | Only with CEO / Legal approval |
| Regulators | Formal notification | Per regulatory deadlines |

---

## 11. Evidence Preservation

- All logs, forensic images, and incident artefacts must be preserved in tamper-evident form.
- Evidence must not be deleted or modified during or after an incident investigation.
- Chain of custody must be maintained for all evidence that may be required for legal proceedings.

---

## 12. Testing and Exercises

- The CIRP must be tested at least **annually** through a tabletop exercise or simulation.
- Key contact information and offline copies of this plan must be verified at each test.
- Exercise outcomes and gaps are documented and used to improve the plan.

---

## 13. Exceptions

Deviations from this plan during a live incident must be documented in the incident log with justification. Post-incident review will assess whether deviations were appropriate and whether the plan requires amendment.

---

## 14. Enforcement

All personnel are required to report suspected incidents immediately. Failure to report a known incident, deliberate obstruction of incident response, or destruction of evidence may result in disciplinary action up to and including termination and referral to law enforcement.

---

## 15. Related Documents

| Document ID | Title |
|---|---|
| POL-001 | Cybersecurity Policy |
| POL-002 | Access Control Policy |
| POL-003 | Asset Management Policy |
| POL-004 | Backup and Recovery Policy |
| POL-007 | Vulnerability and Patch Management Policy |

---

## 16. Revision History

| Version | Date | Author | Description of Change |
|---|---|---|---|
| 1.0 | [DD/MM/YYYY] | [Name, Role] | Initial release |

---

## 17. Approval

| Role | Name | Signature | Date |
|---|---|---|---|
| Policy Owner (CISO) | | | |
| Approved by (CEO) | | | |
| Legal / Compliance Review | | | |
