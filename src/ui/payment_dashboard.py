"""Giao diện thanh toán tương thích ngược."""
import streamlit as st
from src.ui.payment import render_payment_component

if __name__ == "__main__":
    st.set_page_config(page_title="Hệ Thống Thanh Toán & Dashboard", layout="wide")
    render_payment_component()
