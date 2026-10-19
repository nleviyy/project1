"""Shared CSS styling and helper UI widgets."""
import streamlit as st


def apply_custom_styles():
    """Apply modern, cohesive styling to the application."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&family=Playfair+Display:wght@600;700&display=swap');

        html, body, [class*="css"], .stApp {
            font-family: "Be Vietnam Pro", sans-serif !important;
        }

        /* Card styles */
        .fnb-card {
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 16px;
            padding: 20px;
            background: rgba(255, 255, 255, 0.04);
            backdrop-filter: blur(8px);
            margin-bottom: 16px;
            transition: all 0.2s ease-in-out;
        }

        .fnb-card:hover {
            border-color: rgba(255, 200, 87, 0.4);
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
        }

        /* Badge styles */
        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 13px;
            font-weight: 600;
        }
        .badge-available { background: rgba(34, 197, 94, 0.18); color: #4ade80; border: 1px solid #22c55e; }
        .badge-occupied { background: rgba(239, 68, 68, 0.18); color: #f87171; border: 1px solid #ef4444; }
        .badge-reserved { background: rgba(234, 179, 8, 0.18); color: #facc15; border: 1px solid #eab308; }

        .badge-pending { background: rgba(234, 179, 8, 0.18); color: #facc15; border: 1px solid #eab308; }
        .badge-preparing { background: rgba(249, 115, 22, 0.18); color: #fb923c; border: 1px solid #f97316; }
        .badge-served { background: rgba(59, 130, 246, 0.18); color: #60a5fa; border: 1px solid #3b82f6; }
        .badge-completed { background: rgba(34, 197, 94, 0.18); color: #4ade80; border: 1px solid #22c55e; }
        .badge-cancelled { background: rgba(148, 163, 184, 0.18); color: #cbd5e1; border: 1px solid #94a3b8; }

        /* Menu item typography */
        .item-price {
            font-size: 18px;
            font-weight: 700;
            color: #ffc857;
        }

        .kitchen-timer {
            font-size: 14px;
            color: #94a3b8;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
