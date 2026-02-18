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

URL donmain:
https://www.thejakartapost.com/business/ 

With index page that can change the last number to select page as followed:
https://www.thejakartapost.com/business/latest?page=1
https://www.thejakartapost.com/business/latest?page=2