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