import streamlit as st


st.markdown(
    '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.5.3/dist/css/bootstrap.min.css" integrity="sha384-TX8t27EcRE3e/ihU7zmQxVncDAy5uIKz4rEkgIXeMed4M0jlfIDPvg6uqKI2xXr2" crossorigin="anonymous">',
    unsafe_allow_html=True,
)
query_params = st.experimental_get_query_params()
tabs = ["Рынок", "Запуск", "Комментарии"]
if "tab" in query_params:
    st.session_state.active_tab = query_params["tab"][0]
else:
    st.session_state.active_tab = "Рынок"

if st.session_state.active_tab not in tabs:
    st.experimental_set_query_params(tab="Рынок")
    st.session_state.active_tab = "Рынок"

li_items = "".join(
    f"""
    <li class="nav-item">
        <a class="nav-link{' active' if t==st.session_state.active_tab else ''}" href="/">{t}</a>
    </li>
    """
    for t in tabs
)
tabs_html = f"""
    <ul class="nav nav-tabs">
    {li_items}
    </ul>
"""

st.markdown(tabs_html, unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)
st.markdown('''<style>
    a {
        color: #1f2229;
    }

    a:hover {
        color: white;
    }
</style>''', unsafe_allow_html=True)

