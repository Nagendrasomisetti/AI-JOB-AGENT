# 🚀 AI Job Agent

This project started with a simple problem:

Finding good ML/AI jobs daily is time-consuming, repetitive, and inefficient.

So instead of manually searching across platforms, I built an **autonomous AI job agent** that does the work for me.

---

## 💡 What this project does

This system automatically:

* Searches for **Machine Learning / AI / Data Science jobs**
* Collects data from multiple platforms
* Extracts important details like:

  * Job title
  * Company
  * Location
  * Skills
  * Salary (if available)
  * Apply link
* Filters out irrelevant jobs
* Removes duplicates
* Ranks jobs based on quality
* Stores them in a database
* Shows everything in a clean dashboard

Instead of scrolling through job portals, I just open the dashboard and see the **best opportunities first**.

---

## 🧠 How it works (high level)

The system works like a pipeline:

1. **Planning (optional AI step)**

   * Uses Gemini API to understand the goal
   * Falls back to rule-based logic if API fails

2. **Data Collection**

   * Scrapes jobs using Selenium from:

     * Internshala
     * Wellfound

3. **Data Processing**

   * Cleans raw data
   * Filters relevant jobs
   * Removes duplicates

4. **Scoring System**

   * Assigns a score to each job based on:

     * Title relevance
     * Skills match (Python, ML, etc.)
     * Salary
     * Other signals
   * Sorts jobs so the best ones appear first

5. **Database Storage**

   * Stores jobs in SQLite
   * Avoids duplicates using unique job links
   * Keeps history of all jobs

6. **Incremental Updates**

   * Each run only saves **new jobs**
   * No repeated data

7. **Dashboard (Streamlit)**

   * Displays jobs in a simple UI
   * Search + filter functionality
   * Clickable apply links
   * Button to fetch latest jobs

---

## 🖥️ Dashboard

(Add screenshots here)

The dashboard shows:

* Total jobs
* Top-ranked opportunities
* Search bar to filter jobs
* Direct apply links

---

## ⚙️ Key Features

* 🔄 **Fully automated job collection**
* 🧠 **AI-assisted filtering (with fallback)**
* 📊 **Job ranking system**
* 🗃️ **Database persistence**
* 🚫 **Duplicate prevention**
* ⚡ **Incremental updates (only new jobs)**
* 🌐 **Interactive dashboard**
* 🔘 **Run agent directly from UI**

---

## 🧠 Why I built this

I noticed I was:

* Repeating the same job searches every day
* Missing good opportunities
* Spending time on irrelevant listings

So I built a system that:

```text
Finds → Filters → Ranks → Shows → Stores
```

Now I only focus on applying, not searching.

---

## ⚠️ Challenges I faced

* Dynamic websites (had to use Selenium instead of requests)
* Unreliable LLM responses (added fallback system)
* Handling duplicate data across runs
* Designing a useful scoring system
* Managing performance vs accuracy

---

## 📈 What I learned

This project helped me understand:

* How to design **end-to-end systems**
* How to combine:

  * AI (LLMs)
  * Automation (Selenium)
  * Data pipelines
  * Databases
  * UI (Streamlit)
* Why real systems need:

  * Fallbacks
  * Error handling
  * Incremental updates

---

## 🚀 Future Improvements

* Add more job platforms
* Improve scoring with AI-based ranking
* Faster scraping (parallel execution)
* Better UI (filters, sorting, analytics)
* Deploy online

---

## 🧩 Final Thought

This is not just a scraper.

It’s a small **autonomous system** that:

* Collects data
* Makes decisions
* Improves efficiency

And most importantly, it solves a real problem I face daily.

---

## ▶️ How to run

```bash
pip install -r requirements.txt
streamlit run dashboard.py
```

---

## 🙌

If you find this useful, feel free to fork or build on top of it.
