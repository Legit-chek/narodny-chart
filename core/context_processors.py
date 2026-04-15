from datetime import datetime


def branding(request):
    return {
        "brand_name": "Народный чарт",
        "current_year": datetime.now().year,
    }
