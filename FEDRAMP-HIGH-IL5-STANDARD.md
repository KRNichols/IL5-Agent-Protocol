# FedRAMP High / DoD Impact Level 5
## Complete Build-Against, Scan, and Certification Guide

**Document status:** Working implementation guide compiled 4 September 2026  
**Audience:** Cloud service provider (CSP) engineering, GRC, 3PAO-facing package owners, and DoD mission sponsors  
**Purpose:** One file that names every standard, scan, overlay, artifact, clock, and authorization step required so a High / IL5 package is not missing a hidden requirement at assessment time.

> **Read this first.** There is no official “FedRAMP Impact Level 5.” FedRAMP uses Low / Moderate / High, and in 2026 Certification Classes A–D (Class D = High). “Impact Level 5 (IL5)” is a Department of Defense Cloud Computing Security Requirements Guide (CC SRG / CSP SRG) designation administered by DISA. IL5 is **FedRAMP High plus DoD overlays plus architecture constraints**. Building only to FedRAMP High fails an IL5 assessment. Building to IL5 from day one includes FedRAMP High.

**Two buyer paths. Do not mix them.**

| You are… | You need… | You do not need… |
|---|---|---|
| A **cloud service provider** selling a CSO that DoD missions will run on | FedRAMP High / Class D + DISA IL5 PA + mission ATO + BCAP | CMMC as a substitute for the PA |
| A **defense contractor** holding CUI on *your own* enclave (COCO) | DFARS 252.204-7012, NIST SP 800-171, CMMC Level 2 (or 3), SPRS, 72-hour DIBNet reporting | A DISA IL5 PA. IL5 is not available for contractor-owned systems |
| Handling **ITAR / USML** technical data | US-person ops + typically GovCloud / Azure Government / GCC-High style tenancy | Assuming IL5 automatically equals ITAR authorization (DDTC / 22 CFR 120–130 is separate) |

FedRAMP RFC-0020 “Certified Level 5” is High package-depth language. It is not DoD IL5.

**Do not treat blog control counts as the baseline.** Download the current official workbooks listed in §2 and implement those. Counts in this file are directional so you can staff and budget. Official counts live in:

- FedRAMP High / Class D: SSP Appendix A High + FedRAMP Security Controls Baseline (Excel) + [fedramp.gov/2026/reference/fedramp-certification](https://fedramp.gov/2026/reference/fedramp-certification/)
- DoD overlay: *DoD Rev 5 SSP Addendum Controls v1.2* and *DoD SRG Control Crosswalk* on [public.cyber.mil/dccs/dccs-documents](https://public.cyber.mil/dccs/dccs-documents/)
- NSS overlay: CNSSI 1253 (29 July 2022 and later attachments) on [cnss.gov](https://www.cnss.gov/CNSS/issuances/Instructions.cfm)

---

## Table of contents

1. [Terminology and decision tree](#1-terminology-and-decision-tree)
2. [Official source library (download these)](#2-official-source-library-download-these)
3. [Categorization — FIPS 199, NSS, CUI](#3-categorization--fips-199-nss-cui)
4. [The four-layer control stack](#4-the-four-layer-control-stack)
5. [FedRAMP High / Class D control families](#5-fedramp-high--class-d-control-families)
6. [DoD FedRAMP+ / Table D-1 / SSP Addendum](#6-dod-fedramp--table-d-1--ssp-addendum)
7. [CNSSI 1253 NSS overlays](#7-cnssi-1253-nss-overlays)
8. [Non-control IL5 architecture requirements](#8-non-control-il5-architecture-requirements)
9. [Cryptography (FIPS 140-3 sunset)](#9-cryptography-fips-140-3-sunset)
10. [Identity, CAC/PIV, Credential Strength D](#10-identity-cacpiv-credential-strength-d)
11. [Network: BCAP, SCCA, NIPRNet, SNAP](#11-network-bcap-scca-niprnet-snap)
12. [Personnel, citizenship, screening](#12-personnel-citizenship-screening)
13. [STIG / SRG / SCAP / ACAS hardening](#13-stig--srg--scap--acas-hardening)
14. [Scan program — types, cadence, evidence](#14-scan-program--types-cadence-evidence)
15. [Penetration test and red team](#15-penetration-test-and-red-team)
16. [POA&M, deviations, remediation clocks](#16-poam-deviations-remediation-clocks)
17. [Continuous monitoring calendar](#17-continuous-monitoring-calendar)
18. [Incident reporting clocks](#18-incident-reporting-clocks)
19. [Logging (M-21-31 and successors)](#19-logging-m-21-31-and-successors)
20. [Significant change process](#20-significant-change-process)
21. [IaaS / PaaS / SaaS shared responsibility](#21-iaas--paas--saas-shared-responsibility)
22. [Inheritance, CRM, GovCloud / Azure Government](#22-inheritance-crm-govcloud--azure-government)
23. [Package artifacts and SSP appendices](#23-package-artifacts-and-ssp-appendices)
24. [3PAO assessment mechanics](#24-3pao-assessment-mechanics)
25. [Authorization sequence: FedRAMP then DISA PA then ATO](#25-authorization-sequence-fedramp-then-disa-pa-then-ato)
26. [FedRAMP 2026 / 20x transition dates](#26-fedramp-2026--20x-transition-dates)
27. [Related regimes that are not IL5 (CMMC, 800-171, ITAR, CJIS)](#27-related-regimes-that-are-not-il5-cmmc-800-171-itar-cjis)
28. [Common failure modes](#28-common-failure-modes)
29. [Build order and staffing checklist](#29-build-order-and-staffing-checklist)
30. [Contacts, portals, and mailboxes](#30-contacts-portals-and-mailboxes)
31. [Revision and verification notes](#31-revision-and-verification-notes)

---

## 1. Terminology and decision tree

### 1.1 What the words actually mean

| Term | Who owns it | What it covers |
|---|---|---|
| FedRAMP Low / Moderate / High | GSA FedRAMP PMO + agency AO or JAB | Civilian federal cloud authorization against NIST SP 800-53 Rev 5 tailored baselines |
| FedRAMP Class A / B / C / D | FedRAMP Consolidated Rules for 2026 | New certification-class language. Class B ≈ Low, Class C ≈ Moderate, Class D ≈ High |
| FedRAMP 20x | FedRAMP PMO | Modernized continuous-validation path (KSIs, machine-readable evidence). Class D 20x is still rolling out |
| RFC-0020 “Certified Level 5” | FedRAMP RFC language | Package-depth label mapping to High. **Not DoD IL5** |
| DoD Impact Level 2 | DISA CC SRG | Public / non-CUI DoD data. FedRAMP Moderate floor |
| DoD Impact Level 4 | DISA CC SRG | CUI / non-critical mission data. FedRAMP Moderate or High + FedRAMP+ |
| **DoD Impact Level 5** | DISA CC SRG | Higher-sensitivity CUI and unclassified NSS / NSI. **FedRAMP High floor** + FedRAMP+ + (if NSS) CNSSI 1253 |
| DoD Impact Level 6 | DISA CC SRG | SECRET. Dedicated classified infrastructure, SIPRNet, not commercial FedRAMP |
| DoD Provisional Authorization (PA) | DISA AO | Reusable authorization that a mission owner can leverage |
| Agency / Mission ATO | Agency or DoD Authorizing Official | System-specific Authority to Operate under RMF (NIST SP 800-37 / DoDI 8510.01) |
| 3PAO | FedRAMP-recognized assessor | Independent assessor for FedRAMP packages; often reused for DISA delta |
| FedRAMP+ | DISA CSP SRG Appendix D | DoD parameter values and extra C/CEs on top of FedRAMP |
| NSS | CNSS / NIST SP 800-59 | National Security System. Triggers CNSSI 1253 overlays |

### 1.2 Decision tree (do this before writing a single control)

```
What data will the CSO process, store, or transmit?
├─ Public / non-CUI DoD          → IL2 (FedRAMP Moderate)
├─ Ordinary CUI, not NSS         → IL4 (FedRAMP Moderate or High + FedRAMP+)
├─ Higher-sensitivity CUI
│     or unclassified NSS/NSI    → IL5 (FedRAMP High + FedRAMP+ + NSS if designated)
└─ SECRET or above               → IL6 (stop; this guide does not apply)

Is the system an NSS under NIST SP 800-59?
├─ No, but AO still wants IL5    → FedRAMP High + IL5 non-NSS FedRAMP+ + SRG architecture
└─ Yes                           → FedRAMP High + IL5 NSS FedRAMP+ + CNSSI 1253 Table D-1 “+” H-H-x
                                    (~600 controls, not ~410)

Who is the customer?
├─ Civilian agency only          → FedRAMP High / Class D may be sufficient
├─ DoD mission on commercial cloud → FedRAMP High THEN DISA IL5 PA THEN mission ATO
└─ Both                          → Build IL5; civilian agencies can reuse the High package
```

Get the categorization and NSS determination **in writing from the sponsoring AO**. That memo is the most expensive page in the program.

### 1.3 Approximate control counts (directional only)

Industry analysis of CSP SRG v1r3 (2 July 2025) and FedRAMP Rev 5 High:

| Stack | FedRAMP | DoD SRG extras | CNSSI 1253 “+” H-H-x | Approx total |
|---|---|---|---|---|
| FedRAMP Moderate | 323 | — | — | 323 |
| FedRAMP High / Class D | 410 | — | — | **410** |
| FedRAMP High + IL4 FedRAMP+ | 410 | ~18 | — | ~428 |
| FedRAMP High + IL5 (non-NSS, older Table 2 language) | 410 | ~10–21 | — | ~420–431 |
| **FedRAMP High + IL5 NSS** | 410 | ~20 | ~170 | **~600** |
| FedRAMP High + IL6 NSS | 410 | ~19 | ~170 + classified overlay ~29 | ~628 |

Microsoft Learn and older CC SRG v1r4 still say Table 2 required **10 additional C/CEs** beyond FedRAMP High for an IL5 PA. Current CSP SRG language for IL5 NSS is stricter and pulls in CNSSI 1253. **Use the SSP Addendum on cyber.mil as the source of truth.**

---

## 2. Official source library (download these)

### 2.1 FedRAMP

| Artifact | Where |
|---|---|
| Class D / High certification rules and control list | https://fedramp.gov/2026/reference/fedramp-certification/ |
| Full Rev 5 control reference with FedRAMP parameters | https://fedramp.gov/2026/reference/controls/ |
| Rev 5 documents and templates | https://www.fedramp.gov/rev5/documents-templates/ |
| Rev 5 playbooks (Getting Started, Authorization, ConMon, Agency) | https://fedramp.gov/docs/rev5/ |
| SSP Appendix A — High FedRAMP Security Controls | Rev5 templates library (Word) |
| FedRAMP High / Moderate / Low / LI-SaaS SSP template | Rev5 templates library |
| SAR Appendix A Risk Exposure Table (RET) | Rev5 templates library (Excel) |
| SAR Appendix B High Security Requirements Traceability Matrix | Rev5 templates library |
| High Readiness Assessment Report (RAR) template | Rev5 templates library |
| POA&M template | Rev5 templates library (Excel) |
| Vulnerability Deviation Request Form | Rev5 templates library (Excel) |
| Continuous Monitoring Playbook (v1.0, 17 Nov 2025) | https://www.fedramp.gov/resources/documents/Continuous_Monitoring_Playbook.pdf |
| Continuous Monitoring Deliverables Template | Rev5 templates library |
| Annual Assessment Controls Selection Worksheet | Rev5 templates library |
| Penetration Test Guidance | https://www.fedramp.gov/resources/documents/CSP_Penetration_Test_Guidance.pdf |
| Vulnerability scanning (legacy playbook page) | https://fedramp.gov/legacy/playbook/csp/continuous-monitoring/vulnerability-scanning/ |
| Vulnerability Detection and Response (CR26) | https://fedramp.gov/2026/reference/rev5/b/vulnerability-detection-and-response/ |
| Incident Evaluation and Communication (CR26) | https://fedramp.gov/2026/reference/incident-evaluation-and-communication/ |
| Significant Change Notifications | https://www.fedramp.gov/docs/significant-change-notifications/ |
| 2026 Consolidated Rules timeline | https://fedramp.gov/2026/timeline/ |
| 3PAO Obligations and Performance Standards | FedRAMP resources/documents |
| FedRAMP Marketplace | https://marketplace.fedramp.gov/ |

### 2.2 DoD / DISA

| Artifact | Where | Library date noted |
|---|---|---|
| DCCS home | https://public.cyber.mil/dccs/ | — |
| DCCS document library | https://public.cyber.mil/dccs/dccs-documents/ | — |
| Cloud Computing SRG (current zip) | DCCS library | 2026-06-26 |
| DoD Rev 5 SSP Addendum Controls v1.2 | DCCS library | 2025-12-03 |
| DoD SRG Control Crosswalk | DCCS library | 2026-04-23 |
| DoD DISA CSP Architecture Briefing Preparation Guide | DCCS library | 2026-04-21 |
| Cloud CSP Onboarding / Questionnaire | DCCS library | 2026-08-11 / 2026-04-27 |
| SOP for CSP Submitting eMASS Controls for Validation | DCCS library | 2026-06-03 |
| DoD Cloud Authorization Process (June 2024) | DCCS library | 2024-06-24 |
| DoD Cloud Authorization Process Diagram | DCCS library | 2025-05-09 |
| Cloud Change / Extension / EOL / IATT forms | DCCS library | 2026-06-04 |
| DISN Connection Process Guide | https://dl.dod.cyber.mil/wp-content/uploads/connect/CPG/ConnProcGuide.html | — |
| STIGs / SRGs | https://public.cyber.mil/stigs/ | quarterly |
| Cloud Computing Mission Owner Network SRG | STIG portal / cyber.trackr.live mirror | — |

### 2.3 NIST / CNSS / crypto / identity

| Artifact | Where |
|---|---|
| NIST SP 800-53 Rev 5.2.0 catalog | https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final |
| NIST SP 800-53B baselines | CSRC |
| NIST SP 800-53A Rev 5.2.0 assessment procedures | CSRC |
| OSCAL catalog (machine-readable) | https://github.com/usnistgov/oscal-content |
| NIST SP 800-37 Rev 2 RMF | CSRC |
| NIST SP 800-59 identifying NSS | CSRC |
| NIST SP 800-60 Vol I/II categorization | CSRC |
| NIST SP 800-115 technical testing | CSRC |
| NIST SP 800-70 National Checklist Program | CSRC |
| NIST SP 800-52 Rev 2 TLS | CSRC |
| NIST SP 800-63 digital identity | CSRC |
| FIPS 199, FIPS 200 | CSRC |
| FIPS 140-3 / CMVP validated modules | https://csrc.nist.gov/projects/cryptographic-module-validation-program |
| CNSSI 1253 + overlays | https://www.cnss.gov/CNSS/issuances/Instructions.cfm |
| CNSSP 32 (NSS ↔ FedRAMP High floor) | CNSS |
| DoDI 8510.01 RMF | https://www.esd.whs.mil/DD/ |
| DoDI 8500.01 Cybersecurity | esd.whs.mil |
| DoDI 8520.03 Identity | esd.whs.mil |
| DoDI 8530.01 CSSP / DTM-24-001 | esd.whs.mil |
| DoDI 5200.48 CUI | esd.whs.mil |
| DoDI 8551.01 PPSM | esd.whs.mil |

---

## 3. Categorization — FIPS 199, NSS, CUI

### 3.1 FIPS 199 (FedRAMP High water mark)

Score Confidentiality, Integrity, and Availability independently as Low / Moderate / High. The system impact level is the **high-water mark**. One High objective makes the whole system High.

FedRAMP High is for severe or catastrophic adverse effect on operations, assets, or individuals.

The **agency customer**, not the vendor, sets the impact level for FedRAMP. For DoD, the mission AO sets the Impact Level under the SRG.

### 3.2 CNSSI 1253 (NSS — CIA chosen independently)

NSS categorization does **not** use the high-water mark the same way. Confidentiality, Integrity, and Availability are selected independently. IL5 typically accommodates NSS/CUI up to moderate confidentiality and moderate integrity in older SRG language (M-M-x). Later CSP SRG NSS language for IL5 uses FedRAMP High + CNSSI 1253 Table D-1 “+” with H-H-x selections. **The AO’s written categorization wins.**

NIST SP 800-59 decides whether the system is an NSS. If it is, CNSSI 1253 and CNSSP 32 apply. CNSSP 32 makes FedRAMP High the floor for unclassified NSS in commercial cloud.

### 3.3 CUI vs NSS vs elevated CUI

- CUI is defined by 32 CFR 2002 and the NARA CUI Registry; DoD implements via DoDI 5200.48.
- Ordinary CUI often lands at IL4.
- CUI the AO judges needs more protection than IL4, plus unclassified NSS/NSI, lands at IL5.
- Export-controlled CUI (ITAR/EAR), certain personnel records, and mission-critical planning data are the usual IL5 drivers.
- Privacy / PII / PHI may add the CNSSI 1253 Privacy Overlay on top of whatever IL you are in.

### 3.4 What you produce in this step

- FIPS 199 worksheet (SSP Appendix K)
- Written AO categorization memo (CIA + IL + NSS yes/no + applicable overlays)
- Information types list from NIST SP 800-60 / CUI Registry
- Data-flow diagram showing every place that data at that categorization exists

---

## 4. The four-layer control stack

```
Layer 4  CNSSI 1253 overlays (NSS, Privacy, ICS, CDS, Classified-if-ever)
Layer 3  DoD CSP SRG FedRAMP+ parameters + extra C/CEs + SRG non-control requirements
Layer 2  FedRAMP High / Class D  (~410 NIST SP 800-53 Rev 5 C/CEs + FedRAMP parameters)
Layer 1  NIST SP 800-53 Rev 5 catalog + 800-53B High baseline + 800-53A test cases
```

You implement from the top of the catalog downward, but you **assess** from Layer 2 up. A FedRAMP High P-ATO does not automatically grant IL4 or IL5. DISA still assesses Layers 3 and 4 and every non-control SRG requirement (location, citizenship, BCAP, STIGs).

---

## 5. FedRAMP High / Class D control families

Source: FedRAMP Consolidated Rules Class D list + SSP Appendix A High. Implement from the official Appendix A. This section is the working checklist of High-weight IDs so engineering can see the shape of the baseline.

Assign **every** organization-defined parameter. Empty assignments fail.

### 5.1 Access Control (AC)

- AC-01 Policy and Procedures
- AC-02 Account Management  
  AC-02(01) Automated System Account Management  
  AC-02(02) Automated Temporary and Emergency Account Management  
  AC-02(03) Disable Accounts  
  AC-02(04) Automated Audit Actions  
  AC-02(05) Inactivity Logout  
  AC-02(07) Privileged User Accounts  
  AC-02(09) Restrictions on Use of Shared and Group Accounts  
  AC-02(11) Usage Conditions  
  AC-02(12) Account Monitoring for Atypical Usage  
  AC-02(13) Disable Accounts for High-risk Individuals
- AC-03 Access Enforcement
- AC-04 Information Flow Enforcement  
  AC-04(04) Flow Control of Encrypted Information  
  AC-04(21) Physical or Logical Separation of Information Flows
- AC-05 Separation of Duties
- AC-06 Least Privilege  
  AC-06(01) Authorize Access to Security Functions  
  AC-06(02) Non-privileged Access for Nonsecurity Functions  
  AC-06(03) Network Access to Privileged Commands  
  AC-06(05) Privileged Accounts  
  AC-06(07) Review of User Privileges  
  AC-06(08) Privilege Levels for Code Execution  
  AC-06(09) Log Use of Privileged Functions  
  AC-06(10) Prohibit Non-privileged Users from Executing Privileged Functions
- AC-07 Unsuccessful Logon Attempts
- AC-08 System Use Notification
- AC-10 Concurrent Session Control
- AC-11 Device Lock + AC-11(01) Pattern-hiding Displays
- AC-12 Session Termination
- AC-14 Permitted Actions Without Identification or Authentication
- AC-17 Remote Access  
  AC-17(01) Monitoring and Control  
  AC-17(02) Protection of Confidentiality and Integrity Using Encryption  
  AC-17(03) Managed Access Control Points  
  AC-17(04) Privileged Commands and Access
- AC-18 Wireless Access  
  AC-18(01) Authentication and Encryption  
  AC-18(03) Disable Wireless Networking  
  AC-18(04) Restrict Configurations by Users  
  AC-18(05) Antennas and Transmission Power Levels
- AC-19 Access Control for Mobile Devices + AC-19(05) Full Device or Container-based Encryption
- AC-20 Use of External Systems  
  AC-20(01) Limits on Authorized Use  
  AC-20(02) Portable Storage Devices — Restricted Use
- AC-21 Information Sharing
- AC-22 Publicly Accessible Content

**IL5 pressure points:** AC-04 flow isolation, AC-06 privileged path, AC-17(03) managed access points (this is where BCAP lands), AC-07 lockout (DoD overrides to 3 tries for privileged).

### 5.2 Awareness and Training (AT)

- AT-01 Policy and Procedures
- AT-02 Literacy Training and Awareness  
  AT-02(02) Insider Threat  
  AT-02(03) Social Engineering and Mining
- AT-03 Role-based Training
- AT-04 Training Records

### 5.3 Audit and Accountability (AU)

- AU-01 Policy and Procedures
- AU-02 Event Logging
- AU-03 Content of Audit Records + AU-03(01) Additional Audit Information
- AU-04 Audit Log Storage Capacity
- AU-05 Response to Audit Logging Process Failures  
  AU-05(01) Storage Capacity Warning  
  AU-05(02) Real-time Alerts
- AU-06 Audit Record Review, Analysis, and Reporting  
  AU-06(01) Automated Process Integration  
  AU-06(03) Correlate Audit Record Repositories  
  AU-06(04) Central Review and Analysis  
  AU-06(05) Integrated Analysis of Audit Records  
  AU-06(06) Correlation with Physical Monitoring  
  AU-06(07) Permitted Actions
- AU-07 Audit Record Reduction and Report Generation + AU-07(01) Automatic Processing
- AU-08 Time Stamps
- AU-09 Protection of Audit Information  
  AU-09(02) Store on Separate Physical Systems or Components  
  AU-09(03) Cryptographic Protection  
  AU-09(04) Access by Subset of Privileged Users
- AU-10 Non-repudiation
- AU-11 Audit Record Retention
- AU-12 Audit Record Generation + AU-12(01) + AU-12(03) Changes by Authorized Individuals

**IL5 pressure points:** centralized correlation, crypto-protected logs on separate components, time sync to authoritative source (see also SC-45), retention aligned to §19.

### 5.4 Assessment, Authorization, and Monitoring (CA)

- CA-01 Policy and Procedures
- CA-02 Control Assessments  
  CA-02(01) Independent Assessors  
  CA-02(02) Specialized Assessments *(Class D / High)*  
  CA-02(03) Leveraging Results from External Organizations
- CA-03 Information Exchange + CA-03(06) Transfer Authorizations
- CA-06 Authorization
- CA-07 Continuous Monitoring  
  CA-07(01) Independent Assessment  
  CA-07(04) Risk Monitoring
- CA-08 Penetration Testing  
  CA-08(01) Independent Penetration Testing Agent or Team  
  **CA-08(02) Red Team Exercises** *(High / Class D — separate from annual pentest)*
- CA-09 Internal System Connections

### 5.5 Configuration Management (CM)

- CM-01 Policy and Procedures
- CM-02 Baseline Configuration  
  CM-02(02) Automation Support for Accuracy and Currency  
  CM-02(03) Retention of Previous Configurations  
  CM-02(07) Configure Systems and Components for High-risk Areas
- CM-03 Configuration Change Control  
  CM-03(01) Automated Documentation, Notification, and Prohibition of Changes  
  CM-03(02) Testing, Validation, and Documentation of Changes  
  CM-03(04) Security and Privacy Representatives  
  CM-03(06) Cryptography Management
- CM-04 Impact Analyses  
  CM-04(01) Separate Test Environments  
  CM-04(02) Verification of Controls
- CM-05 Access Restrictions for Change  
  CM-05(01) Automated Access Enforcement and Audit Records  
  CM-05(05) Privilege Limitation for Production and Operation
- CM-06 Configuration Settings  
  CM-06(01) Automated Management, Application, and Verification  
  CM-06(02) Respond to Unauthorized Changes
- CM-07 Least Functionality  
  CM-07(01) Periodic Review  
  CM-07(02) Prevent Program Execution  
  CM-07(05) Authorized Software — Allow-by-exception
- CM-08 System Component Inventory  
  CM-08(01) Updates During Installation and Removal  
  CM-08(02) Automated Maintenance  
  CM-08(03) Automated Unauthorized Component Detection  
  CM-08(04) Accountability Information
- CM-09 Configuration Management Plan
- CM-10 Software Usage Restrictions
- CM-11 User-installed Software
- CM-12 Information Location + CM-12(01) Automated Tools to Support Information Location
- CM-14 Signed Components

**IL5 pressure points:** CM-06 = STIGs (see §13). CM-07(05) allow-by-exception (DoD DSPAV often required). CM-08 inventory must match every scan target.

### 5.6 Contingency Planning (CP)

- CP-01 Policy and Procedures
- CP-02 Contingency Plan  
  CP-02(02) Capacity Planning  
  CP-02(03) Resume Mission and Business Functions  
  CP-02(05) Continue Mission and Business Functions  
  CP-02(08) Identify Critical Assets
- CP-03 Contingency Training + CP-03(01) Simulated Events
- CP-04 Contingency Plan Testing + CP-04(02) Alternate Processing Site
- CP-06 Alternate Storage Site  
  CP-06(01) Separation from Primary Site  
  CP-06(02) Recovery Time and Recovery Point Objectives  
  CP-06(03) Accessibility
- CP-07 Alternate Processing Site  
  CP-07(01) Separation from Primary Site  
  CP-07(02) Accessibility  
  CP-07(03) Priority of Service  
  CP-07(04) Preparation for Use
- CP-08 Telecommunications Services  
  CP-08(01) Priority of Service Provisions  
  CP-08(02) Single Points of Failure  
  CP-08(03) Separation of Primary and Alternate Providers  
  CP-08(04) Provider Contingency Plan
- CP-09 System Backup  
  CP-09(01) Testing for Reliability and Integrity  
  CP-09(02) Test Restoration Using Sampling  
  CP-09(03) Separate Storage for Critical Information  
  CP-09(05) Transfer to Alternate Storage Site  
  CP-09(08) Cryptographic Protection
- CP-10 System Recovery and Reconstitution  
  CP-10(02) Transaction Recovery  
  CP-10(04) Restore Within Time Period

IL5 also expects crisis-survivable operations (SRG continuity language). Alternate sites must still meet US-location and tenancy rules.

### 5.7 Identification and Authentication (IA)

- IA-01 Policy and Procedures
- IA-02 Identification and Authentication (Organizational Users)  
  IA-02(01) MFA to Privileged Accounts  
  IA-02(02) MFA to Non-privileged Accounts  
  IA-02(05) Individual Authentication with Group Authentication  
  IA-02(06) Access to Accounts — Separate Device  
  IA-02(08) Access to Accounts — Replay Resistant  
  IA-02(12) Acceptance of PIV Credentials
- IA-03 Device Identification and Authentication
- IA-04 Identifier Management + IA-04(04) Identify User Status
- IA-05 Authenticator Management  
  IA-05(01) Password-based Authentication  
  IA-05(02) Public Key-based Authentication  
  IA-05(06) Protection of Authenticators  
  IA-05(07) No Embedded Unencrypted Static Authenticators  
  IA-05(08) Multiple System Accounts  
  IA-05(13) Expiration of Cached Authenticators
- IA-06 Authentication Feedback
- IA-07 Cryptographic Module Authentication
- IA-08 Identification and Authentication (Non-organizational Users)  
  IA-08(01) Acceptance of PIV Credentials from Other Agencies  
  IA-08(02) Acceptance of External Authenticators  
  IA-08(04) Use of Defined Profiles
- IA-11 Re-authentication
- IA-12 Identity Proofing  
  IA-12(02) Identity Evidence  
  IA-12(03) Identity Evidence Validation and Verification  
  IA-12(04) In-person Validation and Verification  
  IA-12(05) Address Confirmation

See §10 for DoDI 8520.03 Strength D (hardware token / PKI). IA-05(01) is a common DSPAV override.

### 5.8 Incident Response (IR)

- IR-01 Policy and Procedures
- IR-02 Incident Response Training  
  IR-02(01) Simulated Events  
  IR-02(02) Automated Training Environments
- IR-03 Incident Response Testing
- IR-04 Incident Handling  
  IR-04(01) Automated Incident Handling Processes  
  IR-04(02) Dynamic Reconfiguration  
  IR-04(04) Information Correlation  
  IR-04(06) Insider Threats  
  IR-04(11) Integrated Incident Response Team
- IR-05 Incident Monitoring + IR-05(01) Automated Tracking, Data Collection, and Analysis
- IR-06 Incident Reporting  
  IR-06(01) Automated Reporting  
  IR-06(03) Supply Chain Coordination
- IR-07 Incident Response Assistance + IR-07(01) Automation Support
- IR-08 Incident Response Plan
- IR-09 Information Spillage Response  
  IR-09(02) Training  
  IR-09(03) Post-spill Operations  
  IR-09(04) Exposure to Unauthorized Personnel

Clocks are in §18. DoD adds CSSP coordination and CJCSM 6510.01 / DFARS 204.73.

### 5.9 Maintenance (MA)

- MA-01 Policy and Procedures
- MA-02 Controlled Maintenance + MA-02(02) Automated Maintenance Activities
- MA-03 Maintenance Tools  
  MA-03(01) Inspect Tools  
  MA-03(02) Inspect Media  
  MA-03(03) Prevent Unauthorized Removal
- MA-04 Nonlocal Maintenance + MA-04(03) Comparable Security and Sanitization
- MA-05 Maintenance Personnel + MA-05(01) Individuals Without Appropriate Access
- MA-06 Timely Maintenance

Nonlocal maintenance of IL5 systems cannot originate from non-US / non-cleared staff over the open internet.

### 5.10 Media Protection (MP)

- MP-01 Policy and Procedures
- MP-02 Media Access
- MP-03 Media Marking
- MP-04 Media Storage
- MP-05 Media Transport
- MP-06 Media Sanitization  
  MP-06(01) Review, Approve, Track, Document, and Verify  
  MP-06(02) Equipment Testing  
  MP-06(03) Nondestructive Techniques
- MP-07 Media Use

CUI marking follows DoDI 5200.48. Sanitization evidence is a favorite 3PAO sample.

### 5.11 Physical and Environmental Protection (PE)

- PE-01 Policy and Procedures
- PE-02 Physical Access Authorizations
- PE-03 Physical Access Control + PE-03(01) System Access
- PE-04 Access Control for Transmission
- PE-05 Access Control for Output Devices
- PE-06 Monitoring Physical Access  
  PE-06(01) Intrusion Alarms and Surveillance Equipment  
  PE-06(04) Monitoring Physical Access to Systems
- PE-08 Visitor Access Records + PE-08(01) Automated Records Maintenance and Review
- PE-09 Power Equipment and Cabling
- PE-10 Emergency Shutoff
- PE-11 Emergency Power + PE-11(01) Alternate Power Supply — Minimal Operational Capability
- PE-12 Emergency Lighting
- PE-13 Fire Protection  
  PE-13(01) Detection Systems — Automatic Activation and Notification  
  PE-13(02) Suppression Systems — Automatic Activation and Notification
- PE-14 Environmental Controls + PE-14(02) Monitoring with Alarms and Notifications
- PE-15 Water Damage Protection + PE-15(01) Automation Support
- PE-16 Delivery and Removal
- PE-17 Alternate Work Site
- PE-18 Location of System Components

For commercial CSPs, many PE controls are inherited from the IaaS/colocation provider — but only if that provider is inside the authorization boundary or a leveraged FedRAMP/IL5 CSO. PE-18 is where US-location is documented.

### 5.12 Planning (PL)

- PL-01 Policy and Procedures
- PL-02 System Security and Privacy Plans
- PL-04 Rules of Behavior + PL-04(01) Social Media and External Site/Application Usage Restrictions
- PL-08 Security and Privacy Architectures
- PL-10 Baseline Selection
- PL-11 Baseline Tailoring

PL-08 architecture narrative must describe tenant isolation, key management, and BCAP paths in enough detail that a 3PAO can pentest them.

### 5.13 Personnel Security (PS)

- PS-01 Policy and Procedures
- PS-02 Position Risk Designation
- PS-03 Personnel Screening + PS-03(03) Information Requiring Special Protective Measures
- PS-04 Personnel Termination + PS-04(02) Automated Actions
