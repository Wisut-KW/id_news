# AGENTS.md — Jakarta Post 

(Python script version)

---

# 1. Objective

Build a **Python-script for news scraping** that:

* Scrapes Jakarta Post news website
* Date range defaults to last **2 days**
* Allows configurable date range
* Paginates until date threshold reached
* append output to json data file
* do not append existing URL
* Logs error

# 2. Source Categories

Base domain:

[https://www.thejakartapost.com/business/companies/latest?utm_source=(direct)&utm_medium=channel_companies](https://www.thejakartapost.com/business/companies/latest?utm_source=%28direct%29&utm_medium=channel_companies)