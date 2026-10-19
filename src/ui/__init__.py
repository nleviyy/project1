"""Package UI: Chứa các component giao diện người dùng Streamlit."""
from .common import apply_custom_styles
from .dashboard import render_dashboard_component
from .kitchen import render_kitchen_component
from .ordering import render_ordering_component
from .orders import render_orders_component
from .payment import render_payment_component
from .tables import render_tables_component


def render_ordering_ui():
    """Hàm wrapper tương thích ngược cho giao diện đặt món."""
    render_ordering_component()


__all__ = [
    "apply_custom_styles",
    "render_ordering_component",
    "render_tables_component",
    "render_kitchen_component",
    "render_orders_component",
    "render_payment_component",
    "render_dashboard_component",
    "render_ordering_ui",
]