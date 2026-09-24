import streamlit as st
import requests

# ============================================================
# CONFIGURAZIONE
# ============================================================

st.set_page_config(
    page_title="Training Hub",
    page_icon="💪",
    layout="centered",
    initial_sidebar_state="collapsed"
)

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}"
}


# ============================================================
# FUNZIONE SUPABASE
# ============================================================

def supabase_get(table, params=None):
    url = f"{SUPABASE_URL}/rest/v1/{table}"

    response = requests.get(
        url,
        headers=HEADERS,
        params=params,
        timeout=10
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# CARICAMENTO ALLENAMENTO
# ============================================================

def load_training():

    # --------------------------------------------------------
    # ATLETA TEST
    # --------------------------------------------------------

    athletes = supabase_get(
        "athletes",
        {
            "select": "*",
            "email": "eq.marco.test@traininghub.local"
        }
    )

    if not athletes:
        return None

    athlete = athletes[0]

    # --------------------------------------------------------
    # PROGRAMMA ASSEGNATO
    # --------------------------------------------------------

    assignments = supabase_get(
        "athlete_programs",
        {
            "select": "program_id",
            "athlete_id": f"eq.{athlete['id']}",
            "active": "eq.true"
        }
    )

    if not assignments:
        return None

    program_id = assignments[0]["program_id"]

    programs = supabase_get(
        "programs",
        {
            "select": "*",
            "id": f"eq.{program_id}"
        }
    )

    if not programs:
        return None

    program = programs[0]

    # --------------------------------------------------------
    # ALLENAMENTO
    # --------------------------------------------------------

    workouts = supabase_get(
        "workouts",
        {
            "select": "*",
            "program_id": f"eq.{program_id}",
            "order": "workout_order.asc"
        }
    )

    if not workouts:
        return None

    workout = workouts[0]

    # --------------------------------------------------------
    # ESERCIZI DELL'ALLENAMENTO
    # --------------------------------------------------------

    workout_exercises = supabase_get(
        "workout_exercises",
        {
            "select": "*",
            "workout_id": f"eq.{workout['id']}",
            "order": "exercise_order.asc"
        }
    )

    exercise_data = []

    for we in workout_exercises:

        exercises = supabase_get(
            "exercises",
            {
                "select": "*",
                "id": f"eq.{we['exercise_id']}"
            }
        )

        if not exercises:
            continue

        exercise = exercises[0]

        sets = supabase_get(
            "prescribed_sets",
            {
                "select": "*",
                "workout_exercise_id": f"eq.{we['id']}",
                "order": "set_number.asc"
            }
        )

        exercise_data.append(
            {
                "workout_exercise": we,
                "exercise": exercise,
                "sets": sets
            }
        )

    return {
        "athlete": athlete,
        "program": program,
        "workout": workout,
        "exercises": exercise_data
    }


# ============================================================
# DESIGN
# ============================================================

st.markdown(
    """
    <style>

    .stApp {
        background: #090b0e;
        color: white;
    }

    .block-container {
        max-width: 680px;
        padding-top: 2rem;
        padding-bottom: 6rem;
    }

    .brand {
        color: #ff3b3f;
        font-size: 13px;
        font-weight: 900;
        letter-spacing: 2px;
        margin-bottom: 3px;
    }

    .hello {
        font-size: 32px;
        font-weight: 900;
        line-height: 1.1;
        margin-bottom: 5px;
    }

    .subtitle {
        color: #969ba5;
        margin-bottom: 24px;
    }

    .workout-card {
        background: #14171c;
        border: 1px solid #292d34;
        border-radius: 18px;
        padding: 22px;
        margin-top: 10px;
        margin-bottom: 20px;
    }

    .tag {
        color: #ff4b4f;
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 1px;
        margin-bottom: 4px;
    }

    .workout-title {
        color: white;
        font-size: 28px;
        font-weight: 900;
        margin-bottom: 4px;
    }

    .workout-info {
        color: #a1a6af;
        font-size: 15px;
    }

    .exercise-card {
        background: #14171c;
        border: 1px solid #292d34;
        border-radius: 16px;
        padding: 18px;
        margin-top: 20px;
        margin-bottom: 10px;
    }

    .exercise-number {
        color: #ff4b4f;
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 1px;
    }

    .exercise-title {
        color: white;
        font-size: 22px;
        font-weight: 800;
        margin-top: 3px;
    }

    .exercise-category {
        color: #979ca5;
        font-size: 14px;
        margin-top: 2px;
    }

    .prescription {
        background: #101216;
        border: 1px solid #242830;
        border-radius: 10px;
        padding: 11px 14px;
        margin-top: 12px;
        margin-bottom: 5px;
        color: #e5e7eb;
    }

    div.stButton > button {
        width: 100%;
        min-height: 50px;
        border-radius: 12px;
        border: none;
        background: #e63236;
        color: white;
        font-weight: 800;
        font-size: 15px;
    }

    div.stButton > button:hover {
        background: #f23b40;
        color: white;
        border: none;
    }

    div[data-testid="stNumberInput"] input {
        background-color: #14171c;
        color: white;
    }

    div[data-testid="stTextArea"] textarea {
        background-color: #14171c;
        color: white;
    }

    hr {
        border-color: #292d34;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# LETTURA DATI
# ============================================================

try:
    data = load_training()

except Exception as e:
    st.error("Errore nel collegamento con Supabase.")
    st.code(str(e))
    st.stop()


if not data:
    st.error("Nessun programma trovato.")
    st.stop()


athlete = data["athlete"]
program = data["program"]
workout = data["workout"]
exercise_data = data["exercises"]


# ============================================================
# HOME ATLETA
# ============================================================

st.markdown(
    '<div class="brand">TRAINING HUB</div>',
    unsafe_allow_html=True
)

st.markdown(
    f'<div class="hello">Ciao, {athlete["first_name"]} 👋</div>',
    unsafe_allow_html=True
)

st.markdown(
    f'<div class="subtitle">{program["name"]}</div>',
    unsafe_allow_html=True
)


# ============================================================
# CARD ALLENAMENTO
# ============================================================

workout_name = workout["name"]
exercise_count = len(exercise_data)
estimated_minutes = workout.get("estimated_minutes") or "--"

workout_card = (
    '<div class="workout-card">'
    '<div class="tag">ALLENAMENTO</div>'
    f'<div class="workout-title">{workout_name}</div>'
    f'<div class="workout-info">'
    f'{exercise_count} {"esercizio" if exercise_count == 1 else "esercizi"}'
    f' &nbsp; • &nbsp; circa {estimated_minutes} min'
    '</div>'
    '</div>'
)

st.markdown(
    workout_card,
    unsafe_allow_html=True
)


# ============================================================
# PULSANTE INIZIA
# ============================================================

if st.button(
    "▶ INIZIA ALLENAMENTO",
    key="start_training"
):
    st.session_state["training_started"] = True


# ============================================================
# ALLENAMENTO APERTO
# ============================================================

if st.session_state.get("training_started"):

    st.markdown("## Allenamento")

    if not exercise_data:
        st.warning(
            "Non ci sono ancora esercizi assegnati a questo allenamento."
        )

    # --------------------------------------------------------
    # CICLO ESERCIZI
    # --------------------------------------------------------

    for index, item in enumerate(
        exercise_data,
        start=1
    ):

        exercise = item["exercise"]
        we = item["workout_exercise"]
        sets = item["sets"]

        exercise_name = exercise["name"]
        exercise_category = exercise.get("category") or ""

        exercise_card = (
            '<div class="exercise-card">'
            f'<div class="exercise-number">ESERCIZIO {index}</div>'
            f'<div class="exercise-title">{exercise_name}</div>'
            f'<div class="exercise-category">{exercise_category}</div>'
            '</div>'
        )

        st.markdown(
            exercise_card,
            unsafe_allow_html=True
        )

        # ----------------------------------------------------
        # IMMAGINE
        # ----------------------------------------------------

        if exercise.get("image_url"):

            st.image(
                exercise["image_url"],
                use_container_width=True
            )

        # ----------------------------------------------------
        # DESCRIZIONE
        # ----------------------------------------------------

        if exercise.get("description"):

            st.caption(
                exercise["description"]
            )

        # ----------------------------------------------------
        # NOTE COACH
        # ----------------------------------------------------

        if we.get("coach_notes"):

            st.info(
                f"📝 Coach: {we['coach_notes']}"
            )

        # ----------------------------------------------------
        # VIDEO
        # ----------------------------------------------------

        if exercise.get("video_url"):

            st.link_button(
                "▶ GUARDA VIDEO",
                exercise["video_url"]
            )

        # ----------------------------------------------------
        # SERIE PRESCRITTE
        # ----------------------------------------------------

        if sets:

            st.markdown("### Serie")

            for s in sets:

                set_number = s["set_number"]
                target_reps = s.get("target_reps")
                target_weight = s.get("target_weight_kg")

                reps_display = (
                    target_reps
                    if target_reps is not None
                    else "-"
                )

                weight_display = (
                    target_weight
                    if target_weight is not None
                    else "-"
                )

                prescription = (
                    '<div class="prescription">'
                    f'<b>Serie {set_number}</b><br>'
                    f'Prescritto: {reps_display} reps × '
                    f'{weight_display} kg'
                    '</div>'
                )

                st.markdown(
                    prescription,
                    unsafe_allow_html=True
                )

                col1, col2 = st.columns(2)

                with col1:

                    st.number_input(
                        "KG fatti",
                        min_value=0.0,
                        value=float(target_weight or 0),
                        step=2.5,
                        key=f"kg_{we['id']}_{set_number}"
                    )

                with col2:

                    st.number_input(
                        "Reps fatte",
                        min_value=0,
                        value=int(target_reps or 0),
                        step=1,
                        key=f"reps_{we['id']}_{set_number}"
                    )

        else:

            st.caption(
                "Nessuna serie prescritta."
            )

        # ----------------------------------------------------
        # SERIE EXTRA
        # ----------------------------------------------------

        extra_key = f"extra_sets_{we['id']}"

        if extra_key not in st.session_state:
            st.session_state[extra_key] = 0

        if st.button(
            "＋ AGGIUNGI SERIE",
            key=f"add_extra_{we['id']}"
        ):
            st.session_state[extra_key] += 1

        for extra in range(
            st.session_state[extra_key]
        ):

            st.markdown(
                f"#### Serie extra {extra + 1}"
            )

            col1, col2 = st.columns(2)

            with col1:

                st.number_input(
                    "KG",
                    min_value=0.0,
                    value=0.0,
                    step=2.5,
                    key=f"extra_kg_{we['id']}_{extra}"
                )

            with col2:

                st.number_input(
                    "Reps",
                    min_value=0,
                    value=0,
                    step=1,
                    key=f"extra_reps_{we['id']}_{extra}"
                )

        st.markdown("---")


    # ========================================================
    # FINE ALLENAMENTO
    # ========================================================

    st.markdown("## Fine allenamento")

    session_rpe = st.slider(
        "RPE sessione",
        min_value=1,
        max_value=10,
        value=7,
        key="session_rpe"
    )

    athlete_notes = st.text_area(
        "Note allenamento",
        placeholder="Come è andato l'allenamento?",
        key="athlete_notes"
    )

    if st.button(
        "✓ COMPLETA ALLENAMENTO",
        key="complete_training"
    ):

        st.success(
            "Allenamento pronto per essere salvato! 💪"
        )

        st.caption(
            "Nel prossimo passaggio collegheremo questo pulsante "
            "a workout_logs e set_logs."
        )
