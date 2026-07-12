---
id: powerapps
name: Power Apps
category: low_code
summary: Microsoft low-code platform for building custom business apps over Dataverse and 1000+ connectors.
---

# Power Apps

## What it is
Microsoft's **low-code application** platform (part of the Power Platform). Teams build custom
business apps — with real UIs, forms, and data — quickly and with minimal code, governed inside
Microsoft 365 / Entra. It is for **building the app people use**, complementing Alteryx (data
prep) and UiPath (UI automation).

## Core capabilities
- **Canvas apps** (pixel-level UI control) and **model-driven apps** (data-first apps generated
  over the data model).
- **Dataverse** as a governed data platform, plus **1000+ connectors** to SharePoint, SQL,
  Office, and third-party SaaS.
- **Forms, data entry, approvals**, and mobile + web delivery from one app.
- Tight pairing with **Power Automate** (workflow / approvals / Power Automate Desktop RPA) and
  **Power BI** (embedded analytics).
- **Governance** through the Power Platform admin center and **Entra ID** identity.

## Ideal use cases
- **Custom internal / line-of-business apps** for organizations already on Microsoft 365.
- **Replacing spreadsheets, paper, or manual processes** with a governed app (intake, tracking,
  approvals, inspections).
- **Mobile data capture** and field workflows.
- A front-end **form/app on top of** data that Alteryx cleaned or that a robot maintains.

## When NOT to use it (defer elsewhere)
- **High-scale, consumer-facing** products, or apps needing heavy custom UI, complex logic, or
  high performance → build with code.
- Environments that are **not Microsoft-centric**.
- Pure **data preparation / analytics** → use Alteryx.
- **Automating an existing legacy app's UI** rather than building a new one → use UiPath.

## Integration notes
- Backed by **Dataverse** + connectors; **Power Automate** for flows and desktop RPA; **Power
  BI** for reporting; **Entra ID** for auth.
- Frequently the **user-facing layer** of an automation: Power Apps captures/edits data,
  Power Automate/UiPath moves it, Alteryx prepares it, Power BI reports on it.
