---
id: uipath
name: UiPath
category: rpa
summary: Enterprise RPA platform whose software robots automate repetitive, rules-based work across application UIs and legacy systems.
---

# UiPath

## What it is
An enterprise **Robotic Process Automation (RPA)** platform. Software "robots" mimic what a
person does at the screen — clicking, typing, copying between apps — to automate repetitive,
rules-based processes. Its distinctive strength is driving applications **through their UI**,
so it can automate systems that expose **no API** (legacy/mainframe/Citrix, thick-client apps).

## Core capabilities
- **UI automation** across desktop, web, Citrix/virtualized, and legacy applications; robust
  selectors + screen scraping / OCR.
- **Attended** (triggered alongside a human) and **unattended** (fully autonomous) robots.
- **Orchestrator** — deploy, schedule, queue, monitor, and govern robots at scale.
- **Excel, email, and file automation**; **queues** for high-volume transaction processing.
- **Document Understanding + AI/ML activities** for extracting data from semi-structured
  documents (invoices, forms).

## Ideal use cases
- Automating **manual, repetitive, cross-application** processes ("swivel-chair" work:
  re-keying data from system A into system B).
- **Integrating legacy systems that have no API** by driving their UI.
- High-volume **back-office** work: data entry, reconciliation, report pulling, statement
  processing.
- Bridging a gap **now** where a proper integration is too costly or slow to build.

## When NOT to use it (defer elsewhere)
- A clean **API / integration already exists** → call it directly; that's more reliable than
  UI automation.
- Building a **new user-facing application or form** → use Power Apps.
- Heavy **data transformation / blending / analytics** → use Alteryx.
- **Complex bespoke business logic** that is clearer and more maintainable written as code.

## Integration notes
- **Orchestrator** governs credentials, scheduling, and audit for the robot fleet.
- Mix API/connector activities with UI steps; pair with **Document Understanding** for
  semi-structured inputs.
- Often the **execution arm** downstream of a decision: e.g. Alteryx prepares data, a robot
  keys the results into a system that lacks an API.
