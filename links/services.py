import requests
from django.conf import settings

class PSIService:
    API_KEY = 'AIzaSyCTGTYjk95BRnFUOVJmCASsp3FYLw4vZow'
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
        except requests.RequestException as e:
            raise Exception(f"Error fetching PSI report: {str(e)}")
    
    @classmethod
    def fetch_both_reports(cls, url):
        """
        Fetch both mobile and desktop reports for a URL
        """
        mobile_report = cls.fetch_report(url, 'mobile')
        desktop_report = cls.fetch_report(url, 'desktop')
        return mobile_report, desktop_report 