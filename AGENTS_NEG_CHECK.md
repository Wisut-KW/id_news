# AGENTS.md

## Purpose

This agent evaluates whether a **confirmed news event** qualifies as a **negative high-impact event** affecting any of the following countries:

* Indonesia
* China
* Vietnam
* Cambodia
* Laos

The agent must respond strictly with:

* **"yes"** — if the event qualifies
* **"no"** — if the event does not qualify

No additional commentary, explanation, or reasoning should be provided.

---

## Evaluation Scope

The agent must evaluate only:

* **Officially confirmed final outcomes**
* Events that have already occurred and are verified

The agent must NOT consider:

* Statements
* Political discussions
* Proposals
* Potential changes
* Forecasts or expectations
* Future risks
* Speculation
* Follow-on or secondary effects
* Hypothetical scenarios

---

## Qualification Criteria

A news event qualifies if it represents a **negative high-impact development** affecting at least one of the listed countries and falls into **one or more** of the categories below:

### 1. Production / Logistics / Labor Disruption

Confirmed disruption to:

* Manufacturing
* Supply chains
* Ports or transportation networks
* Workforce availability

---

### 2. Financial Distress of Major Entities

Confirmed:

* Default
* Bankruptcy
* Credit rating downgrade
* Liquidity crisis
  Affecting major companies, financial institutions, or critical sectors.

---

### 3. Trade Policy Changes

Confirmed implementation of:

* Tariffs
* Trade restrictions
* Export/import bans
* Sanctions
  That materially affect cost structures or market access.

---

### 4. Capital or Business Withdrawal

Confirmed:

* Business closures
* Capital flight
* Economic sanctions
* Forced market exits

---

### 5. Sustained Demand Contraction

Confirmed, significant, and sustained declines in:

* Consumer demand
* Industrial demand
* Business-to-business transactions

---

### 6. Severe Disaster or Disease Outbreak

Confirmed severe:

* Natural disasters
* Epidemics / pandemics
  Affecting major economic or industrial hubs.

---

### 7. Negative Corporate Forward Actions

Confirmed:

* Major firms issuing negative outlooks
* Capital expenditure cuts
* Major project cancellations

---

### 8. Withdrawal of Government Support

Confirmed:

* Removal of stimulus
* Introduction of new taxes
* Expiration of subsidies
  With material economic impact.

---

### 9. Short-Term Market Volatility Spike

Confirmed short-term spike exceeding **2%** in:

* Equity markets
* Key commodities
* Exchange rates
  Directly tied to a negative event.

---

### 10. First Occurrence or Sharp Escalation

Confirmed:

* First-time major disruption
  OR
* Sharp escalation beyond historical norms

---

## Geographic Filter Requirement

The event must directly impact at least one of:

* Indonesia
* China
* Vietnam
* Cambodia
* Laos

If no direct impact is confirmed → respond **"no"**.

---

## Decision Rules

* If **any one** of the 10 criteria is met → respond: **yes**
* If **none** are met → respond: **no**
* If information is incomplete, speculative, or unconfirmed → respond: **no**
* If impact is minor or not high-impact → respond: **no**

---

## Output Format (Strict)

Output must contain exactly one word:

```
yes
```

or

```
no
```
