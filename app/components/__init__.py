from .banner import banner_reglas
from .forms import render_schedule_form, render_results
from .dashboard import (
    render_historical_data, 
    render_weekly_summary,
    render_weekly_statistics  # ← NUEVA IMPORTACIÓN
)

__all__ = [
    "banner_reglas",
    "render_schedule_form", 
    "render_results",
    "render_historical_data",
    "render_weekly_summary",
    "render_weekly_statistics"  # ← NUEVA
]