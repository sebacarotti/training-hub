import streamlit as st
import requests
st.set_page_config(
    page_title="Training Hub",
    page_icon="💪",
    layout="centered",
    initial_sidebar_state="collapsed"
)
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}"
}


def supabase_get(table, params=None):
    url = f"{SUPABASE_URL}/rest/v1/{table}"

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=10
    )

    response.raise_for_status()

    return response.json()
st.markdown("""
<style>
    .stApp {
        background-color: #0b0d10;
        color: white;
    }

    .block-container {
        max-width: 650px;
        padding-top: 2rem;
        padding-bottom: 5rem;
    }

    .brand {
        color: #ff3131;
        font-size: 14px;
        font-weight: 800;
        letter-spacing: 2px;
        margin-bottom: 4px;
    }

    .hello {
        font-size: 32px;
        font-weight: 800;
        margin-bottom: 2px;
    }

    .week {
        color: #9ca3af;
        margin-bottom: 25px;
    }

    .workout-card {
        background: #15181d;
        border: 1px solid #292d34;
        border-radius: 18px;
        padding: 22px;
        margin-bottom: 20px;
    }

    .tag {
        color: #ff4b4b;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 1px;
    }

    .workout-title {
        font-size: 27px;
        font-weight: 800;
        margin-top: 5px;
    }

    .details {
        color: #a5aab2;
        margin-top: 5px;
    }

    .exercise-card {
        background: #15181d;
        border: 1px solid #292d34;
        border-radius: 14px;
        padding: 16px 18px;
        margin: 10px 0;
    }

    .exercise-name {
        font-size: 18px;
        font-weight: 700;
    }

    .exercise-info {
        color: #9ca3af;
        font-size: 14px;
        margin-top: 4px;
    }

    div.stButton > button {
        width: 100%;
        border-radius: 12px;
        height: 50px;
        background: #e52b2f;
        color: white;
        border: none;
        font-weight: 800;
        font-size: 16px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="brand">TRAINING HUB</div>', unsafe_allow_html=True)
st.markdown('<div class="hello">Ciao, Marco 👋</div>', unsafe_allow_html=True)
st.markdown('<div class="week">Programma Test</div>', unsafe_allow_html=True)

st.markdown("""
<div class="workout-card">
    <div class="tag">ALLENAMENTO DI OGGI</div>
    <div class="workout-title">Lower Body</div>
    <div class="details">5 esercizi &nbsp; • &nbsp; circa 55 min</div>
</div>
""", unsafe_allow_html=True)

if st.button("▶  INIZIA ALLENAMENTO"):
    st.session_state["started"] = True

if st.session_state.get("started"):

    st.markdown("### Esercizi")

    exercises = [
        ("Front Squat", "5 serie • 2 min recupero"),
        ("Romanian Deadlift", "4 serie"),
        ("Bulgarian Split Squat", "3 serie"),
        ("Nordic Hamstring", "3 serie"),
        ("Standing Calf Raise", "4 serie")
    ]

    for name, info in exercises:
        st.markdown(
            f"""
            <div class="exercise-card">
                <div class="exercise-name">{name}</div>
                <div class="exercise-info">{info}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("### Front Squat")

    prescribed_sets = [
        (1, 6, 50),
        (2, 5, 60),
        (3, 4, 70),
        (4, 1, 90),
        (5, 2, 100)
    ]

    for set_number, reps, weight in prescribed_sets:
        st.markdown(f"**Serie {set_number} — {reps} reps × {weight} kg**")

        c1, c2 = st.columns(2)

        with c1:
            st.number_input(
                "KG realizzati",
                min_value=0.0,
                value=float(weight),
                step=2.5,
                key=f"kg_{set_number}"
            )

        with c2:
            st.number_input(
                "Reps realizzate",
                min_value=0,
                value=reps,
                step=1,
                key=f"reps_{set_number}"
            )

    if st.button("＋ AGGIUNGI SERIE"):
        st.info("Qui aggiungeremo una serie extra.")

    st.slider(
        "RPE sessione",
        min_value=1,
        max_value=10,
        value=7
    )

    st.text_area(
        "Note allenamento",
        placeholder="Come è andato l'allenamento?"
    )

    if st.button("✓ COMPLETA ALLENAMENTO"):
        st.success("Allenamento completato!")
st.markdown("---")
st.markdown("### 🔌 Test connessione Supabase")

try:

    sets_db = supabase_get(
        "prescribed_sets",
        {
            "select": "set_number,target_reps,target_weight_kg",
            "order": "set_number.asc"
        }
    )

    if sets_db:

        st.success("Supabase collegato correttamente! ✅")

        for serie in sets_db:

            st.write(
                f"Serie {serie['set_number']} → "
                f"{serie['target_reps']} reps × "
                f"{serie['target_weight_kg']} kg"
            )

    else:
        st.warning("Connessione riuscita, ma non ho trovato serie.")

except Exception as e:

    st.error("Errore nella connessione a Supabase")
    st.code(str(e))
