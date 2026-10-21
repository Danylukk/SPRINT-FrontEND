"""Registro de páginas para navegação contextual entre ficha e chat."""
import streamlit as st

PAGES = {}


def open_chat():
    st.switch_page(PAGES["chat"])
