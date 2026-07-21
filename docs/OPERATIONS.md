# LeadForge AI — Sheets Edition operations

## Runtime services

Only two containers run: `api` and `web`. Google Sheets is the sole source of truth for leads and analysis results.

## Credential setup

1. Enable the Google Sheets API in the Google Cloud project.
2. Create a service account and download its JSON key.
3. Share the target spreadsheet with the JSON key's `client_email` as Editor.
4. Save the key as `services/api/secrets/google-service-account.json`.
5. Keep `.env` and `services/api/secrets/` private; both are ignored by Git.

## Running

Run `docker compose up --build`, then browse to `http://localhost:3002`. The service creates headings only when the `Leads` tab is empty. Discoveries append to the sheet, and analysis updates the score, priority, and issues columns of the same lead.

## Compliance

Use discovery and enrichment providers within their API terms, respect rate limits, and obtain lawful marketing consent before outreach. Do not scrape Google Maps or private social data.
