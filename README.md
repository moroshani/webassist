# WebAssist

[![CI](https://github.com/yourusername/webassist/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/webassist/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/django-4.2%2B-green.svg)](https://www.djangoproject.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/yourusername/webassist.svg)](https://github.com/yourusername/webassist/commits/main)

---

WebAssist is a Django-based web assistant for monitoring, analyzing, and improving your websites. It features a unified dashboard, advanced analytics, per-user API key management, and deep SSL/security checks.

## Features

- **Unified Dashboard**: Manage all your sites and see key metrics (PSI, uptime, SSL, etc.) at a glance
- **Modular Feature Analytics**: Each feature (Uptime, PSI, SSL, SSL Labs, etc.) has History, Trend, and Compare tabs with charts and tables
- **Per-User API Keys**: Each user manages their own API keys for all services (no global/fallback keys)
- **Uptime Monitoring**: Live status, history, trend, and compare analytics via UptimeRobot
- **PageSpeed Insights**: Google PSI integration with full analytics and export
- **SSL Certificate Checks**: Local SSL inspection and advanced SSL Labs scans, with expiry/grade trends and comparison
- **Export/Import**: Export and import links and reports as CSV/JSON
- **User Management**: Secure authentication, social login, and user settings
- **Modern UI**: Bootstrap 5, Chart.js, responsive design

## Technologies Used

- **Backend**: Django 4.2+, Python 3.10+
- **Frontend**: Bootstrap 5, Chart.js, JavaScript
- **Database**: SQLite (dev), PostgreSQL/MySQL (prod recommended)
- **APIs**: Google PageSpeed Insights, UptimeRobot, SSL Labs

## Badges

- CI: GitHub Actions runs tests, lint, and type checks on every push
- Python: 3.10+
- Django: 4.2+
- License: MIT
- Last Commit: Always up to date

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/webassist.git
   cd webassist
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up environment variables:
   - Create a `.env` file in the project root with at least:
     ```env
     DJANGO_SECRET_KEY=your_django_secret_key
     PSI_API_KEY=your_pagespeed_insights_api_key
     UPTIMEROBOT_API_KEY=your_uptimerobot_api_key
     ```
   - The app will not start unless these are set.
5. Run migrations:
   ```bash
   python manage.py migrate
   ```
6. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```
7. Run the development server:
   ```bash
   python manage.py runserver
   ```

## Usage

- Access the dashboard at `/dashboard/` (default root)
- Manage your API keys in the user settings page
- Use the Features button for each site to access all available features (Uptime, PSI, SSL, etc.)
- Each feature page provides History, Trend, and Compare analytics
- Export/import links and reports from the dashboard
- Admin interface available at `/admin/`

## Project Structure

```
webassist/
├── links/                    # Main Django app (models, views, services)
├── templates/                # HTML templates (Bootstrap, modular)
├── static/                   # Static files (CSS, JS)
├── webassist/                # Project settings and URLs
├── manage.py                 # Django management script
├── requirements.txt          # Python dependencies
└── ...
```

## Screenshots

<!--
![WebAssist Screenshot](docs/screenshot.png)
-->
*Screenshot not included. Add `docs/screenshot.png` to display here.*

## API Endpoints

- Export Links as JSON: `GET /sites/export/json/`
- Import Links from JSON: `POST /sites/import/json/` (Content-Type: application/json)
- Export Links as CSV: `GET /sites/export/csv/`

## Running Tests

```bash
pytest
```

## Code Style

- Format code: `black .`
- Sort imports: `isort .`
- Type check: `mypy webassist`

## Contributing

Pull requests are welcome! Please open an issue to discuss major changes first. See [CONTRIBUTING.md](../CONTRIBUTING.md) for details.

## Production Best Practices

- Use PostgreSQL or MySQL in production (not SQLite)
- Set all secrets and API keys via environment variables
- Configure logging and monitoring (Sentry, Rollbar, etc.)
- Set up uptime monitoring for your deployed site
- Run regular database backups

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE). 