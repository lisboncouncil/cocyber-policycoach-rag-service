# Network Security Policy

| Field | Value |
|---|---|
| **Document ID** | POL-005 |
| **Version** | 1.0 |
| **Status** | Draft |
| **Classification** | Internal — Restricted |
| **Owner** | IT Manager / CISO |
| **Approved by** | Chief Executive Officer (CEO) |
| **Approval date** | [DD/MM/YYYY] |
| **Next review date** | [DD/MM/YYYY] |
| **Review cycle** | Annual |

---

## 1. Purpose

This policy establishes the requirements for securing [Organisation]'s network infrastructure against unauthorised access, data interception, and disruption. Effective network security is the first line of defence against external attacks and insider threats, preventing adversaries from mapping [Organisation]'s infrastructure, disrupting communications, or reaching critical systems and data. This policy supports compliance with international cybersecurity standards and applicable regulatory obligations.

[Organisation] is committed to continually reviewing and improving its network security controls as part of the ISMS improvement cycle.

---

## 2. Scope

This policy applies to:

- All network components owned, operated, or managed by [Organisation], including firewalls, switches, routers, wireless access points, and VPN gateways
- All network segments, VLANs, and interconnections, including cloud and hybrid environments
- All personnel with access to network management functions
- All devices — managed and unmanaged — connecting to [Organisation]'s networks

---

## 3. Roles and Responsibilities

### 3.1 IT Manager / Network Administrator
- Own and implement this policy across all network infrastructure.
- Maintain and update the network diagram and VLAN documentation.
- Monitor network traffic and investigate anomalies.
- Approve all changes to network devices and configurations.

### 3.2 CISO
- Review network security controls during annual internal audits.
- Approve exceptions to this policy.
- Report network security posture to executive leadership.

### 3.3 All Employees and Contractors
- Connect only authorised devices to [Organisation] networks.
- Report suspected network anomalies or unauthorised access to IT immediately.
- Comply with acceptable use requirements for network resources.

---

## 4. Physical Network Security

- Network components (firewalls, switches, routers) must be installed in dedicated, locked cabinets or secure server rooms.
- Access to network equipment must be restricted to authorised IT personnel only.
- Data and power cables must be protected from physical damage, interference, and unauthorised tapping.
- Physical access to network equipment locations must be logged and reviewed periodically.

---

## 5. Network Segmentation

Networks must be designed with a segmented topology to limit the spread of malware, unauthorised access, and other threats. Network segmentation is implemented through VLANs separated by firewall rules.

### 5.1 Mandatory VLAN Segregation Rules

| Segment | Description |
|---|---|
| **DMZ / Internet-facing** | Systems accepting inbound traffic from the internet (web servers, mail relays) |
| **Network management** | Network device management interfaces; accessible only by IT |
| **Connected services** | Systems accepting inbound traffic from untrusted non-internet networks |
| **End-user devices** | Staff laptops, desktops, and mobile devices |
| **Servers** | Internal servers; separated from end-user VLANs |
| **Unmanaged / Guest devices** | Visitor and BYOD devices; no access to internal resources |
| **Production** | Live business systems |
| **Development / Test** | Development and test environments; isolated from production |
| **Site / Location** | Physical locations separated where applicable |

Traffic between VLANs must be denied by default and explicitly permitted only where a documented business requirement exists.

---

## 6. Firewall Management

- All VLAN boundaries and internet-facing perimeters must be protected by firewalls.
- Firewall rules must follow a **default-deny** policy; all traffic is blocked unless explicitly permitted.
- Outbound internet access for office user VLANs is permitted unless it adversely affects security or performance.
- Traffic prioritisation (QoS) may be applied to prevent recreational streams from affecting business traffic.
- Firewall rule sets must be reviewed at least **annually** and after any significant change.
- All firewall changes must follow the change management process and be documented.

---

## 7. Remote Access and VPN

- Remote access to [Organisation]'s systems must be established via an approved VPN or equivalent encrypted channel.
- VPN access must be configured to require **Multi-Factor Authentication (MFA)** to prevent use of compromised credentials.
- VPN access rights must be managed in accordance with the **Access Control Policy (POL-002)**.
- Machine-to-machine communication over untrusted networks must use VPN or equivalent encryption.

---

## 8. Wired Network Security

- Network ports must be protected from untrusted devices.
- In areas with low physical security, MAC address filtering or network access control (NAC) must be implemented to block or isolate unauthorised devices.
- Unused physical network ports must be disabled.

---

## 9. Wireless Network Security

### 9.1 Approved Encryption Standards (in order of preference)

| Standard | Status |
|---|---|
| **WPA3** | Preferred |
| **WPA2 + AES** | Acceptable |
| **WPA + AES** | Not preferred; replace where feasible |
| **WPA + TKIP** | Not permitted on new deployments |
| **WEP** | Prohibited |
| **Open (unencrypted)** | Prohibited |

### 9.2 Authentication
- Corporate Wi-Fi must authenticate users against a central directory (LDAP or RADIUS preferred).
- Shared PSK-only authentication is not permitted for corporate networks.

### 9.3 Guest Network
- Unmanaged and visitor devices must be restricted to a dedicated **guest VLAN**.
- Guest network traffic must not be able to reach any [Organisation]-managed VLAN or system.
- Guest network access must be time-limited and logged.

---

## 10. Network Management

- A high-level network diagram must be maintained, documenting hardware, function, and IP addressing. The diagram must be updated within **[30 days]** of any significant infrastructure change and stored securely (including an offline copy).
- Network device management interfaces must be:
  - Accessible only by authorised IT personnel.
  - Not exposed to the internet except via VPN.
  - Protected by MFA.
- User access to management ports must be reviewed at least **quarterly**.
- All installations or modifications to network devices must be performed by or in consultation with [Organisation] IT and must follow the change management process.

---

## 11. Network Logging and Monitoring

- All network infrastructure devices must generate logs capturing at minimum: administrator login/logout, configuration changes, and password resets.
- Logs must focus on monitoring traffic flows across network zone boundaries.
- Logs must be retained for a minimum of **[12 months]** and protected against tampering.
- Log anomalies must be investigated promptly. Critical anomalies must be escalated to the CIRT in accordance with the **Cyber Incident Response Plan (POL-008)**.

---

## 12. Intrusion Detection and Prevention (IDS/IPS)

- IDS/IPS must be considered for all critical and confidential network segments where the risk justifies the implementation cost.
- IDS/IPS alerts must be monitored and responded to within defined SLAs based on alert severity.

---

## 13. Service Level Agreements (SLAs)

- SLAs with network service providers must be established for critical and confidential systems to ensure availability and performance commitments.
- SLA compliance must be reviewed at least **quarterly**.

---

## 14. Monitoring and Review

- Network security controls are reviewed during the annual ISMS internal audit.
- The network diagram and VLAN documentation are reviewed and updated at least **annually**.
- Policy effectiveness is presented at the annual ISMS management review.

---

## 15. Exceptions

Exceptions to this policy (e.g., temporary unencrypted wireless, open network ports) require written approval from the CISO, must document the business justification and compensating controls, are time-limited to a maximum of **[30 days]** for security-critical controls, and are recorded in the ISMS exception register.

---

## 16. Enforcement

Unauthorised modification of network devices or configurations, connection of unmanaged devices to internal networks, or disabling of security controls without approval will be treated as a serious disciplinary matter. Wilful circumvention may result in termination and referral to law enforcement.

---

## 17. Related Documents

| Document ID | Title |
|---|---|
| POL-001 | Cybersecurity Policy |
| POL-002 | Access Control Policy |
| POL-003 | Asset Management Policy |
| POL-007 | Vulnerability and Patch Management Policy |
| POL-008 | Cyber Incident Response Plan |

---

## 18. Definitions

| Term | Definition |
|---|---|
| **VLAN** | Virtual Local Area Network — a logically separated network segment. |
| **DMZ** | Demilitarised Zone — a network segment hosting systems accessible from the internet, isolated from internal networks. |
| **NAC** | Network Access Control — a solution that enforces security policies on devices attempting to access the network. |
| **IDS** | Intrusion Detection System — monitors network traffic for suspicious activity and generates alerts. |
| **IPS** | Intrusion Prevention System — monitors and actively blocks detected threats. |
| **QoS** | Quality of Service — traffic prioritisation mechanisms. |
| **MFA** | Multi-Factor Authentication. |
| **RADIUS** | Remote Authentication Dial-In User Service — a network protocol for centralised authentication. |

---

## 19. Compliance and Regulatory References

- **International Cybersecurity Standards** 8.21, 8.22, 8.23
- **Security Controls Framework**
- **CIS Controls v8** — Control 12 (Network Infrastructure Management), Control 13 (Network Monitoring and Defence)
- **CyberFundamentals Framework** — Centre for Cybersecurity Belgium
- **GDPR (EU) 2016/679** — Article 32

---

## 20. Revision History

| Version | Date | Author | Description of Change |
|---|---|---|---|
| 1.0 | [DD/MM/YYYY] | [Name, Role] | Initial release |

---

## 21. Approval

| Role | Name | Signature | Date |
|---|---|---|---|
| Policy Owner (IT Manager / CISO) | | | |
| Approved by (CEO) | | | |
| Compliance Review | | | |
