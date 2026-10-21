import streamlit as st

def render_conversation_list(client, conversations):
    with st.sidebar:
        if st.button("Nova conversa", type="primary", use_container_width=True):
            result = client.create_conversation()
            st.session_state.conversa_ativa = result["id"]
            st.rerun()
        st.markdown("#### Suas conversas")
        if not conversations:
            st.caption("Nenhuma conversa ainda. Crie a primeira para começar.")
        for item in conversations:
            selected = item["id"] == st.session_state.get("conversa_ativa")
            if st.button(item["titulo"], key=f"conversation_{item['id']}",
                         type="primary" if selected else "secondary", use_container_width=True):
                st.session_state.conversa_ativa = item["id"]
                st.rerun()
        st.divider()
        st.caption("Histórico salvo no backend · SQLite")
