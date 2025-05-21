# WebAssist

WebAssist is a Django-based web application for managing and analyzing web links using Google's PageSpeed Insights API. It helps you monitor and improve your website's performance by providing detailed insights and recommendations.

## Features

- **Link Management**: Add, edit, and manage web links with titles, URLs, and descriptions
- **Performance Analysis**: Get comprehensive PageSpeed Insights reports for both mobile and desktop
- **Visual Reports**: View performance metrics with interactive charts and visualizations
- **Historical Data**: Track performance changes over time with stored reports
- **Search & Filter**: Easily find and filter links and reports
- **Real-time Updates**: AJAX-powered refresh functionality

## Technologies Used

- **Backend**: Django 4.x, Python 3.x
- **Frontend**: Bootstrap 5, Chart.js, JavaScript
- **Database**: SQLite
- **APIs**: Google PageSpeed Insights API v5

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/webassist.git
cd webassist
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
# Create a .env file or set these in your environment
PSI_API_KEY=your_pagespeed_insights_api_key
DJANGO_SECRET_KEY=your_django_secret_key
```

# Note: The application will not start unless both variables are set.

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

1. Access the admin interface at `/admin` to manage links
2. View all links at `/sites/`
3. Use the "Fetch PSI" button to get performance reports
4. View detailed reports and metrics in the reports section

## Project Structure

```
webassist/
├── links/                    # Main application
│   ├── models.py            # Database models
│   ├── views.py             # View functions
│   ├── services.py          # PSI API integration
│   └── urls.py              # URL routing
├── templates/               # HTML templates
│   ├── base.html           # Base template
│   └── links/              # App-specific templates
├── static/                 # Static files
│   ├── css/               # Stylesheets
│   └── js/                # JavaScript files
└── manage.py              # Django management script
```

## Screenshots

![WebAssist Screenshot](docs/screenshot.png)

## API Endpoints

- **Export Links as JSON:**
  - `GET /sites/export/json/`
- **Import Links from JSON:**
  - `POST /sites/import/json/` (Content-Type: application/json, body: array of links)
- **Export Links as CSV:**
  - `GET /sites/export/csv/`

## Running Tests

```bash
pytest
```

## Code Style

- Format code with `black .`
- Sort imports with `isort .`
- Type check with `mypy webassist`

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md).

## Production Database Best Practices

- Use PostgreSQL or MySQL in production (not SQLite).
- Set up a managed database service or secure your DB server.
- Use environment variables for DB credentials.
- Run regular backups.

## Logging & Monitoring

- Configure Django logging in `settings.py` to log errors and warnings to file or external service.
- Use a service like Sentry, Rollbar, or similar for error monitoring.
- Set up uptime monitoring (e.g., UptimeRobot, Pingdom) for your deployed site.

## Local Development with .env

You can use a `.env` file in the project root to set environment variables for local development. The project uses [python-dotenv](https://pypi.org/project/python-dotenv/) to load these automatically when running `manage.py`.

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Edit `.env` and fill in your secrets.
3. Run the app as usual. 