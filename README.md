# CareerSpy AI - Autonomous Job Hunter Agent

CareerSpy is an intelligent, autonomous multi-agent system that discovers, extracts, and notifies users about fresh technology and software engineering internship opportunities across the web.

## Overview

CareerSpy leverages **LangGraph**, **Gemini AI**, and **Playwright** to create a fully automated workflow that:
- **Fetches URLs** from multiple sources (Google Sheets + live Google Search via Serper API)
- **Renders & scrapes** JavaScript-heavy career pages with a headless browser
- **Analyzes content** with Google Gemini to extract only IT/Tech internship positions
- **Deduplicates jobs** against a cloud PostgreSQL database
- **Sends email alerts** to team members when fresh opportunities are discovered

---

## Features

✨ **Multi-Source URL Fetching**
- Reads existing links from a configurable Google Sheet
- Discovers new career portals via live Google Search (Serper API)
- Automatically deduplicates combined URL lists

🔍 **Intelligent Web Scraping**
- Uses Playwright for full JavaScript rendering
- Removes boilerplate (scripts, styles, navigation, footers)
- Extracts clean text for AI analysis
- Validates scraped content quality

🧠 **AI-Powered Job Extraction**
- Single Gemini API call processes all content
- JSON schema validation for structured output
- Strict filtering: **only IT/Tech internships**
- Extracts: job title, company source, required skills

💾 **Cloud Database Integration**
- Neon PostgreSQL for persistent job history
- Duplicate detection prevents duplicate notifications
- Automatic table initialization
- Parameterized queries for security

📧 **Smart Email Alerts**
- Sends only when new/fresh vacancies are found
- Beautiful HTML email format with job summary table
- Multi-recipient support
- Gmail SMTP integration with App Password support

---

## Architecture

### Workflow Nodes (LangGraph)

```
fetch_urls_agent 
    ↓
scraper_agent 
    ↓
ai_analyst_agent 
    ↓
END
```

1. **fetch_urls_node** - Combines URLs from Google Sheet and live search
2. **scraper_node** - Renders pages with Playwright, cleans HTML with BeautifulSoup
3. **ai_filter_node** - Sends combined text to Gemini for strict IT/Tech filtering

### State Management

Shared state passed between nodes:
- `urls` - List of URLs to scan
- `current_url_index` - Track progress across URLs
- `current_raw_text` - Combined cleaned HTML text
- `extracted_vacancies` - Final list of job opportunities

### Database Schema

```sql
CREATE TABLE job_history (
    id SERIAL PRIMARY KEY,
    job_title TEXT NOT NULL,
    company_source TEXT NOT NULL,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

---

## Setup & Installation

### Prerequisites
- Python 3.8+
- PostgreSQL database (Neon recommended)
- Google Sheets with job URLs (column 1, starting row 2)
- Google GenAI API key
- Serper API key
- Gmail account with App Password
- Git (optional, for version control)

### 1. Clone the Repository

```bash
git clone <repository-url>
cd agentic-projects
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
# Google GenAI
GOOGLE_API_KEY=<your-google-genai-api-key>

# Serper API for Google Search
SERPER_API_KEY=<your-serper-api-key>

# Google Sheets
# You'll need credentials.json from Google Cloud Console
# Ensure the service account has access to your target Google Sheet

# PostgreSQL / Neon
DATABASE_URL=postgresql://<user>:<password>@<host>:<port>/<database>

# Email Configuration
EMAIL_SENDER=<your-gmail@gmail.com>
EMAIL_PASSWORD=<your-gmail-app-password>  # NOT your regular password
EMAIL_RECEIVERS=["recipient1@example.com", "recipient2@example.com"]  # JSON format
```

### 5. Set Up Google Credentials

1. Create a Google Cloud project
2. Enable the Google Sheets API
3. Create a service account and download the JSON key
4. Save as `credentials.json` in the project root
5. Share your target Google Sheet with the service account email

### 6. Update the Google Sheet ID

In `nodes.py`, line 28, update the Sheet ID:
```python
sheet = gc.open_by_key("YOUR_SHEET_ID_HERE").sheet1
```

---

## Usage

### Run the Agent Locally

```bash
python main.py
```

This will:
1. Initialize the Neon database
2. Build the LangGraph workflow
3. Fetch URLs from Sheet and Google Search
4. Scrape all target pages
5. Extract internships with Gemini
6. Deduplicate against existing jobs
7. Send email alerts for new vacancies

### Run on Schedule (GitHub Actions)

Create `.github/workflows/careersspy.yml`:

```yaml
name: CareerSpy Daily Run

on:
  schedule:
    - cron: '0 9 * * *'  # Run daily at 9 AM UTC

jobs:
  scrape:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: python main.py
        env:
          GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
          SERPER_API_KEY: ${{ secrets.SERPER_API_KEY }}
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          EMAIL_SENDER: ${{ secrets.EMAIL_SENDER }}
          EMAIL_PASSWORD: ${{ secrets.EMAIL_PASSWORD }}
          EMAIL_RECEIVERS: ${{ secrets.EMAIL_RECEIVERS }}
```

---

## File Structure

```
agentic-projects/
├── main.py              # Entry point - orchestrates the workflow
├── graph.py             # LangGraph workflow definition
├── nodes.py             # The three workflow nodes (fetch, scrape, analyze)
├── state.py             # TypedDict for shared state management
├── database.py          # PostgreSQL/Neon helpers
├── notifier.py          # Email alert system
├── search_utils.py      # Serper API integration for Google Search
├── credentials.json     # Google service account (git-ignored)
├── .env                 # Environment variables (git-ignored)
├── requirements.txt     # Python dependencies
└── README.md            # This file
```

---

## Key Dependencies

| Package | Purpose |
|---------|---------|
| **langgraph** | Multi-agent orchestration framework |
| **playwright** | Headless browser automation |
| **beautifulsoup4** | HTML parsing and text extraction |
| **google-genai** | Gemini AI API client |
| **gspread** | Google Sheets API integration |
| **psycopg2** | PostgreSQL client |
| **python-dotenv** | Environment variable management |
| **requests** | HTTP client for Serper API |

---

## How It Works - Detailed Flow

### Phase 1: URL Fetching
1. Read existing URLs from column 1 of Google Sheet (rows 2+)
2. Query Google Search for "software engineer intern jobs Sri Lanka 2026"
3. Filter results (skip LinkedIn feeds, Google root domain)
4. Combine and deduplicate all URLs

### Phase 2: Web Scraping
1. Launch Playwright headless browser
2. For each URL:
   - Navigate with 20s timeout
   - Wait for JS rendering (3s pause)
   - Remove boilerplate: scripts, styles, nav, footer, headers
   - Extract plain text
   - Validate minimum content length (>100 chars)
3. Combine all cleaned text into single document

### Phase 3: AI Analysis
1. Send entire document to Gemini 2.5 Flash model
2. Use strict JSON schema for structured output
3. Filter criteria:
   - **Only IT/Tech domains**: Software Engineering, QA, AI/ML, DevOps, Cloud, Design
   - **Only entry-level roles**: Intern, Trainee, Junior
   - **Exclude non-tech**: Finance, HR, Marketing, Sales, Operations, etc.
4. Extract: job_title, company_source (URL), skills (array)

### Phase 4: Deduplication & Storage
1. For each extracted job:
   - Query Neon DB: does (title, source) combination exist?
   - If new: save to database and add to fresh_jobs list
   - If duplicate: skip and do not notify

### Phase 5: Notifications
1. If fresh_jobs list is non-empty:
   - Build dynamic HTML table with job details
   - Create professional email template
   - Send via Gmail SMTP (TLS, port 587)
   - Notify all EMAIL_RECEIVERS
2. If no fresh jobs:
   - Log status message, skip email send

---

## AI Filtering Logic

The Gemini prompt uses **strict filtering**:

✅ **ALLOWED TECH DOMAINS:**
- Software Engineering / Web Development (React, Node, Python, Java, PHP, Laravel, .NET)
- QA / Software Testing (Manual & Automation)
- AI / Machine Learning / Data Science / Analytics
- Cloud / DevOps / Systems & Network Engineering / IT Support
- UI/UX Design / Product Design

❌ **STRICTLY FORBIDDEN:**
- Finance, Accounting, Management Trainee
- Human Resources, Marketing, Sales, Business Development
- Logistics, Procurement, Administrative, Secretarial
- Operations, Industrial Engineering, Mechanical roles

---

## Troubleshooting

### "SERPER_API_KEY not found"
- Verify `.env` file exists and is in the project root
- Check `SERPER_API_KEY` value is set
- Restart the application after updating `.env`

### "Google Sheet not found"
- Verify the Sheet ID is correct in `nodes.py`
- Check service account email has editor access to the sheet
- Ensure `credentials.json` is valid and in the project root

### "Database initialization failed"
- Verify `DATABASE_URL` is correct in `.env`
- Check PostgreSQL/Neon is running and accessible
- Ensure firewall/security groups allow connections from your IP

### "Email blast failed"
- Verify `EMAIL_PASSWORD` is a Gmail **App Password**, not your regular password
- Enable "Less secure app access" if using Gmail (deprecated but may be needed)
- Check `EMAIL_RECEIVERS` is valid JSON: `["email@example.com"]`
- Verify sender email has SMTP enabled

### "No jobs found"
- Check if target career pages are online and accessible
- Verify Playwright can render JavaScript on those pages
- Review Gemini filtering rules—they may be too strict
- Check logs for specific page error messages

---

## Performance Tips

1. **Batch Size**: Currently scrapes all URLs sequentially. Consider adding async/concurrent scraping for faster runs.
2. **Caching**: Add URL hash caching to avoid re-scraping unchanged pages.
3. **Rate Limiting**: Add delays between requests to avoid blocking.
4. **Logging**: Implement structured logging for better debugging.

---

## Future Enhancements

- [ ] Support for additional job boards (LinkedIn, Indeed, Stack Overflow)
- [ ] Multi-language support beyond English and Sinhala
- [ ] Custom filtering profiles per user
- [ ] Web dashboard for viewing extracted jobs
- [ ] SMS/Slack notifications in addition to email
- [ ] Job application auto-filler
- [ ] Salary estimation and comparison
- [ ] Skills gap analysis

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -m "Add feature"`
4. Push to branch: `git push origin feature/your-feature`
5. Open a Pull Request

---

## License

MIT License - see LICENSE file for details

---

## Author

Created as an autonomous AI agent system for intelligent job discovery in the tech sector.

**Last Updated**: June 2026

---

## Support

For issues, questions, or suggestions:
- Check the Troubleshooting section above
- Review the console output for specific error messages
- Verify all environment variables are set correctly
- Check API key validity and quota limits

---

## Related Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Google GenAI API Docs](https://ai.google.dev/)
- [Playwright Documentation](https://playwright.dev/python/)
- [BeautifulSoup Documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Neon PostgreSQL](https://neon.tech/)
- [Serper API](https://serper.dev/)
