#Sheets Edition

LeadForge AI finds businesses, checks their public websites, scores the opportunity, and writes every lead directly to Google Sheets. This lightweight edition does not use PostgreSQL, MongoDB, Redis, Elasticsearch, or Celery.

## What you need

- Docker Desktop
- A Google Cloud service account with the Google Sheets API enabled
- A Google Places API key with billing enabled, to discover leads with required phone, website, ratings, reviews, and Google Maps URL fields

## Setup

1. In your existing spreadsheet, create or rename the worksheet tab to `Leads`.
2. Create a service account JSON key in Google Cloud and enable the Google Sheets API.
3. Share the spreadsheet with the key file's `client_email` as **Editor**.
4. Save the JSON securely as `services/api/secrets/google-service-account.json`.
5. Run `Copy-Item .env.example .env` and set `GOOGLE_PLACES_API_KEY`.
6. Start with `docker compose up --build`.

Open the dashboard at `http://localhost:3002` and API docs at `http://localhost:8000/docs`.

# Outreach-lead-automation

## Data flow

`Discover businesses → append row to Leads → analyze website → update score and issues in that row → generate personalized outreach`

The first successful connection automatically writes the required column headings to an empty `Leads` tab. Do not commit `.env` or the service account JSON key.

## Discovery

Google Places API is the discovery source. It only stores leads that include a phone number, website URL, and Google Maps URL. Enable billing and the Places API in your Google Cloud project, restrict the server-side API key, and use the data in accordance with the Google Maps Platform terms. Never scrape Google Maps directly.
