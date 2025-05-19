# WebAssist

WebAssist is a Django-based dashboard for tracking, analyzing, and improving the performance, accessibility, and SEO of your web pages using Google's PageSpeed Insights API. It helps you monitor and optimize your sites with detailed, actionable reports and a modern, user-friendly interface.

## Features

- **Page Management**: Add, organize, and manage web pages you want to monitor
- **PageSpeed Insights Integration**: Run audits for mobile and desktop, view all key metrics and scores
- **Performance, Accessibility, Best Practices, SEO**: See scores and details for all Lighthouse categories
- **Historical Tracking**: Keep a history of all PSI runs for each page
- **Search & Filter**: Easily find and filter pages and reports
- **Export**: Download your PSI data as CSV or JSON
- **Modern UI**: Responsive, Bootstrap-based interface

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
# Create a .env file with the following variables
PSI_API_KEY=your_pagespeed_insights_api_key
SECRET_KEY=your_django_secret_key
```

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

1. Access the admin interface at `/admin` to manage pages
2. View all pages at `/pages/`
3. Use the "Fetch PSI" button to get performance reports
4. View detailed reports and metrics in the reports section

## Project Structure

```
webassist/
├── links/                    # Main application
│   ├── models.py             # Page, PSIReport, metrics, and audit models
│   ├── services.py           # PSI API integration and data extraction
│   ├── views.py              # All views for dashboard and reports
│   ├── templates/links/      # All templates (home, page list, reports, partials)
│   └── ...
├── static/                   # Static files (CSS, JS)
├── templates/                # Base templates
├── webassist/                # Project settings and URLs
├── manage.py
└── requirements.txt
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Google PageSpeed Insights API
- Django Framework
- Bootstrap
- Chart.js 