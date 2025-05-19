import requests
from django.conf import settings


class PSIService:
    API_KEY = settings.PSI_API_KEY
    BASE_URL = 'https://www.googleapis.com/pagespeedonline/v5/runPagespeed'

    @classmethod
    def fetch_report(cls, url, strategy='mobile'):
        """
        Fetch PageSpeed Insights report for a given URL and strategy (mobile/desktop)
        """
        params = {
            'url': url,
            'key': cls.API_KEY,
            'strategy': strategy,
            'category': ['performance', 'accessibility', 'best-practices', 'seo'],
        }

        try:
            response = requests.get(cls.BASE_URL, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                raise Exception("API quota exceeded. Please try again later.")
            elif e.response.status_code == 400:
                raise Exception("Invalid URL or request parameters.")
            else:
                raise Exception(f"HTTP error occurred: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error fetching PSI report: {str(e)}")

    @classmethod
    def fetch_both_reports(cls, url):
        """
        Fetch both mobile and desktop reports for a URL
        """
        try:
            mobile_report = cls.fetch_report(url, 'mobile')
            desktop_report = cls.fetch_report(url, 'desktop')
            return mobile_report, desktop_report
        except Exception as e:
            raise Exception(f"Error fetching reports: {str(e)}") 