# Mi Progreso en Español

**Live site:** https://lpetersen4.github.io/spanish_tracking/

A single-page website that visualizes my Spanish study progress, pulling data live from Google Sheets.

## What it tracks

- **Listening** — daily minutes, monthly hours, cumulative hours over time
- **Speaking** — monthly session volume and time per tutor
- **Reading** — books and articles with word counts

## How it works

The page fetches data directly from a Google Sheet (published as CSV) on every load — no backend, no build step. Charts are rendered with [Chart.js](https://www.chartjs.org/).

**Data source:** Google Sheets with three tabs:
- *Daily Log* — listening, reading, and speaking totals per day
- *Speaking* — individual session logs (date, tutor, duration)
- *Reading* — books/articles with word counts and completion dates

## Tech stack

- Vanilla HTML/CSS/JS — a single `index.html` file
- [Chart.js](https://cdn.jsdelivr.net/npm/chart.js) for charts
- [PapaParse](https://www.papaparse.com/) for CSV parsing
- Google Sheets as the data store (public CSV export)

## Running locally

Just open `index.html` in a browser. The Google Sheet must be shared as "Anyone with the link — Viewer" for the CSV fetch to work.
