# 🏆 2026 World Cup Tracker & Autonomous Data Pipeline

A full-stack, real-time tracking dashboard for the 2026 FIFA World Cup. This application is powered by an autonomous data extraction pipeline that dynamically scrapes live match data, calculates group mathematics on the fly, and utilizes headless browser automation to bypass Cloudflare security for high-resolution player statistics.

![Data Pipeline](https://img.shields.io/badge/Data_Pipeline-Online-success?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![Playwright](https://img.shields.io/badge/Playwright-2EAD33?style=for-the-badge&logo=playwright&logoColor=white)

## 🚀 System Architecture

This project is built on a decoupled frontend/backend architecture, emphasizing resilient data engineering and modern UI/UX principles.

* **Frontend:** React + Vite + Tailwind CSS (Glassmorphism & Time-Aware Layouts)
* **Backend:** FastAPI (Python)
* **Database:** PostgreSQL + SQLAlchemy ORM
* **Extraction Engine:** Playwright (Headless Chromium) + BeautifulSoup4 + Requests
* **Automation:** APScheduler (Background Cron Jobs)

## ⚙️ Core Engineering Features

### 1. Autonomous Data Pipeline
A background scheduler runs continuous, asynchronous cron jobs to update the PostgreSQL database without human intervention:
* **Live Score Engine:** Pings hidden ESPN APIs every 60 seconds to catch live match events and score changes.
* **Algorithmic Standings:** Recalculates Group Stage points and goal differentials entirely on the backend every 10 minutes based on the live score DB.
* **Golden Boot Scraper:** Executes a heavily fortified web scraper every 60 minutes to extract the top goalscorers from global sports databases.

### 2. Anti-Bot Security Bypass
The application utilizes **Playwright** to spin up invisible, headless Chromium instances. This allows the backend to mimic real human interaction, dynamically passing Cloudflare browser-verification checks to extract highly protected sports data from sites like Transfermarkt.

### 3. Dynamic Asset Interception & Relational Safety
* **CDN Hijacking:** Intercepts low-resolution image thumbnails from scraped data providers and dynamically rewrites the asset paths to serve high-resolution portraits directly to the React frontend.
* **Entity Isolation:** Implements multi-tiered exact matching and fallback logic to link scraped player data to existing `team_id`s, ensuring strict SQL `NOT NULL` foreign key constraints are never violated during automated syncs.

### 4. Time-Aware UI Bucketing
The React frontend applies dynamic Javascript `Date` logic to incoming data arrays, automatically sorting the UI into intuitive buckets: **Live Now** (featuring glowing CSS animations), **Today's Matches**, **Recent Results**, and **Upcoming Schedule**.

---

## 🛠️ Local Development Setup

### Backend (FastAPI Data Engine)
Navigate to the backend directory and install the Python dependencies. You must also install the Playwright browser binaries for the scraper to function.
```bash
cd backend
pip install -r requirements.txt
playwright install
uvicorn main:app --reload
