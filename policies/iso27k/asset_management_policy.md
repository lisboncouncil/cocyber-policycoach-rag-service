# Asset Management Policy

| Field | Value |
|---|---|
| **Document ID** | POL-003 |
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

This policy establishes guidelines and procedures for the management of information and technology assets at [Organisation], in accordance with international cybersecurity standards, international security controls framework, CIS Controls v8, and IEC 62443. It ensures the availability, integrity, and confidentiality of all physical and digital assets throughout their lifecycle and provides the foundation for risk management, access control, and incident response.

[Organisation] is committed to continuously improving its asset management practices as part of the broader ISMS continual improvement cycle.

---

## 2. Scope

This policy applies to:

- All physical and digital assets owned, operated, or managed by [Organisation]
- All employees, contractors, and third parties involved in the use, management, maintenance, or security of [Organisation]'s assets
- All industrial automation and control systems (IACS) within [Organisation]'s environment

---

## 3. Roles and Responsibilities

### 3.1 Asset Owner
- Maintain the accuracy of asset records in the inventory.
- Identify and communicate security requirements for assigned assets.
- Coordinate maintenance, repair, and decommissioning activities.
- Report any incidents or anomalies relating to assigned assets.

### 3.2 IT Department / [Responsible Department]
- Maintain and update the asset inventory.
- Execute controlled removal and secure disposal of assets.
- Update asset status in all enterprise management systems upon decommissioning.

### 3.3 All Staff (Employees and Contractors)
- Handle all assets with care and in accordance with this policy.
- Report malfunctions, loss, or theft immediately to the asset owner and IT.
- Comply with access management and security requirements for assets in use.

---

## 4. Asset Lifecycle Management

### 4.1 Overview
Asset management covers the following lifecycle phases:

1. **Acquisition / Development** — procurement or creation of new assets
2. **Discovery / Inventory** — identification and cataloguing of assets
3. **Deployment / Use** — authorised use by personnel
4. **Maintenance** — preventive and corrective upkeep
5. **Controlled Removal** — planned decommissioning and disposal
6. **Uncontrolled Removal** — response to loss or theft

### 4.2 Asset Inventory

An up-to-date inventory of all assets must be maintained. The inventory is reviewed by [The Responsible Department] at least every **six months**.

#### 4.2.1 Primary Assets (Information and Data)
Primary assets are the data, information, and knowledge [Organisation] needs to operate. Examples include:

- Business data (orders, contracts, project records)
- Customer data
- Employee personal data
- Proprietary expertise, source code, and product data
- Login credentials and cryptographic keys
- Business processes
- All information classified as confidential

Each primary asset record must include at minimum:

| Field | Description |
|---|---|
| Name | Unique identifier or descriptive name |
| Description | Purpose and nature of the asset |
| Owner | Accountable role or individual |
| Confidentiality / Integrity / Availability classification | CIA rating |
| Personal data indicator | Whether the asset contains personal data |
| Managed by | Team or individual responsible |
| Supplier (if external) | Vendor name and contact information |

#### 4.2.2 Secondary (Supporting) Assets — Hardware
Secondary assets are the systems and infrastructure on which primary assets depend. Hardware inventory must include at minimum:

| Field | Description |
|---|---|
| Asset ID | Unique identifier |
| Purchase date / Depreciation date | |
| Description | |
| Manufacturer, model, serial number | |
| Firmware version | |
| Asset owner (role / business unit) | |
| Physical location | |
| MAC address | |
| Warranty expiry date | |

Virtual and cloud-hosted assets must be included. Administrative items (domain names, certificates, cryptographic keys) must not be omitted.

#### 4.2.3 Secondary (Supporting) Assets — Software
Software inventory must include at minimum:

| Field | Description |
|---|---|
| Name and description | |
| Owner | |
| Version | |
| License information | Contract term, number of licenses |
| Supplier contact and contract number | |
| Data processing dates (if applicable) | |

A distinction must be maintained between **unsupported software** and **unauthorised software**. External SaaS administrators must meet the same requirements contractually.

---

## 5. Use and Maintenance

### 5.1 Authorised Use
- All users must handle assets with care and use them only for authorised purposes.
- [Semi-annual] or more frequent physical or remote inspections of each asset must be performed unless an exception is approved by management.

### 5.2 Preventive Maintenance
- Regular maintenance and security updates must be performed on all endpoints (laptops, desktops, servers, etc.) in accordance with the **Vulnerability and Patch Management Policy (POL-007)**.
- All maintenance activities must be documented in the inventory or a dedicated logbook.

### 5.3 Corrective Maintenance
- Defects or security incidents involving assets must be addressed and documented immediately.
- Root cause analysis and corrective actions must be recorded to prevent recurrence.

---

## 6. Asset Security

### 6.1 Physical Security
Assets must be physically protected against unauthorised access, theft, and damage through access controls, locks, and secure storage.

### 6.2 Network Security
Network segmentation must separate critical IACS components from other segments. Firewalls, IDS/IPS, and other controls must be implemented in accordance with the **Network Security Policy (POL-005)**.

### 6.3 Access Management
Access to assets must comply with the **Access Control Policy (POL-002)** and **Password Policy (POL-006)**.

### 6.4 Data Protection
Sensitive data must be encrypted in transit and at rest. Backups must be performed in accordance with the **Backup and Recovery Policy (POL-004)**.

---

## 7. Asset Disposal and Decommissioning

### 7.1 Controlled Removal
- Assets taken out of service must be returned to [The Responsible Department].
- [The Responsible Department] must:
  - Copy user data if required before disposal.
  - Securely erase all storage media (e.g., cryptographic erasure, physical shredding per DIN 66399, degaussing).
  - Remove all associated documentation (policies, SOPs, manuals) and log the removal.
  - Update all enterprise management systems to reflect decommissioned status.
  - Remove the asset from the inventory with date and method of disposal recorded.

### 7.2 Domain Name Management
- Retired domain names must be retained under [Organisation]'s control for a minimum transition period to prevent domain hijacking.
- Domain name expiry and renewal must be tracked in the asset inventory.

### 7.3 Uncontrolled Removal (Loss or Theft)
- All lost or stolen assets must be reported immediately to [The Responsible Department] and the CISO.
- The asset must be removed from inventory and a security incident recorded in accordance with the **Cyber Incident Response Plan (POL-008)**.

---

## 8. Incident Management

All security incidents involving assets must be immediately reported and documented in accordance with the **Cyber Incident Response Plan (POL-008)**. Incidents must be analysed and corrective actions taken to prevent recurrence.

---

## 9. Training and Awareness

- All employees must receive training on their responsibilities for asset management and security.
- Awareness campaigns must be conducted at least **four times per year**.
- The 10 Golden Rules for Cybersecurity and lessons learned from cyber incidents must be incorporated into training content.

---

## 10. Monitoring and Review

- The asset inventory is reviewed at least every **six months** by [The Responsible Department].
- Compliance with this policy is assessed during annual internal audits.
- Policy effectiveness is reviewed annually by the CISO and presented at management review.

---

## 11. Exceptions

Exceptions to this policy require written approval from the CISO, must document the business justification and compensating controls, are time-limited to a maximum of **12 months**, and are tracked in the ISMS exception register.

---

## 12. Enforcement

Failure to comply with this policy — including failure to report lost or stolen assets, or unauthorised disposal of assets — will be treated as a disciplinary matter in accordance with [Organisation]'s HR policies. Wilful damage or theft of assets may result in dismissal and referral to law enforcement.

---

## 13. Related Documents

| Document ID | Title |
|---|---|
| POL-001 | Cybersecurity Policy |
| POL-002 | Access Control Policy |
| POL-004 | Backup and Recovery Policy |
| POL-005 | Network Security Policy |
| POL-007 | Vulnerability and Patch Management Policy |
| POL-008 | Cyber Incident Response Plan |

---

## 14. Definitions

| Term | Definition |
|---|---|
| **Primary asset** | Information and data that [Organisation] depends on to operate. |
| **Secondary / Supporting asset** | Hardware, software, or services on which primary assets depend. |
| **IACS** | Industrial Automation and Control Systems. |
| **CIA** | Confidentiality, Integrity, Availability — the three core properties of information security. |
| **Degaussing** | Erasing magnetic storage by exposing it to a strong magnetic field. |
| **Asset lifecycle** | The complete set of phases from acquisition through disposal of an asset. |

---

## 15. Compliance and Regulatory References

- **International Cybersecurity Standards** 5.10, 5.11, 5.12, 5.13, 5.14
- **Security Controls Framework**
- **CIS Controls v8** — Control 1 (Inventory and Control of Enterprise Assets), Control 2 (Inventory and Control of Software Assets)
- **IEC 62443** — Industrial cybersecurity standards
- **GDPR (EU) 2016/679** — Article 32

---

## 16. Revision History

| Version | Date | Author | Description of Change |
|---|---|---|---|
| 1.0 | [DD/MM/YYYY] | [Name, Role] | Initial release |

---

## 17. Approval

| Role | Name | Signature | Date |
|---|---|---|---|
| Policy Owner (IT Manager / CISO) | | | |
| Approved by (CEO) | | | |
| Compliance Review | | | |
