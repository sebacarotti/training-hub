import streamlit as st
import requests

# ============================================================
# CONFIG
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
# SUPABASE
# ============================================================

def supabase_get(table, params=None):

    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/{table}",
        headers=HEADERS,
        params=params,
        timeout=10
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# DATI ATLETA
# CACHE = NON RICARICARE TUTTO A OGNI CLICK
# ============================================================

@st.cache_data(ttl=300)
def load_training():

    # --------------------------------------------------------
    # 1. ATLETA
    # --------------------------------------------------------

    athletes = supabase_get(
        "athletes",
        {
            "select": "id,first_name,last_name,email",
            "email": "eq.marco.test@traininghub.local",
            "limit": "1"
        }
    )

    if not athletes:
        return None

    athlete = athletes[0]


    # --------------------------------------------------------
    # 2. PROGRAMMA ASSEGNATO
    # --------------------------------------------------------

    assignments = supabase_get(
        "athlete_programs",
        {
            "select": "program_id",
            "athlete_id": f"eq.{athlete['id']}",
            "active": "eq.true",
            "limit": "1"
        }
    )

    if not assignments:
        return None

    program_id = assignments[0]["program_id"]


    # --------------------------------------------------------
    # 3. PROGRAMMA
    # --------------------------------------------------------

    programs = supabase_get(
        "programs",
        {
            "select": "id,name,description,start_date,end_date",
            "id": f"eq.{program_id}",
            "limit": "1"
        }
    )

    if not programs:
        return None

    program = programs[0]


    # --------------------------------------------------------
    # 4. WORKOUT
    # --------------------------------------------------------

    workouts = supabase_get(
        "workouts",
        {
            "select": (
                "id,name,description,estimated_minutes,"
                "week_number,day_number,workout_order"
            ),
            "program_id": f"eq.{program_id}",
            "order": "workout_order.asc",
            "limit": "1"
        }
    )

    if not workouts:
        return None

    workout = workouts[0]


    # --------------------------------------------------------
    # 5. WORKOUT EXERCISES
    # Una chiamata per TUTTI gli esercizi
    # --------------------------------------------------------

    workout_exercises = supabase_get(
        "workout_exercises",
        {
            "select": (
                "id,exercise_id,exercise_order,"
                "default_rest_seconds,coach_notes"
            ),
            "workout_id": f"eq.{workout['id']}",
            "order": "exercise_order.asc"
        }
    )

    if not workout_exercises:

        return {
            "athlete": athlete,
            "program": program,
            "workout": workout,
            "exercises": []
        }


    # --------------------------------------------------------
    # 6. LIBRERIA ESERCIZI
    # Una sola chiamata
    # --------------------------------------------------------

    exercise_ids = [
        str(item["exercise_id"])
        for item in workout_exercises
    ]

    exercises = supabase_get(
        "exercises",
        {
            "select": (
                "id,name,category,muscle_group,"
                "description,image_url,video_url"
            ),
            "id": f"in.({','.join(exercise_ids)})"
        }
    )


    # --------------------------------------------------------
    # 7. TUTTE LE SERIE
    # Una sola chiamata
    # --------------------------------------------------------

    workout_exercise_ids = [
        str(item["id"])
        for item in workout_exercises
    ]

    prescribed_sets = supabase_get(
        "prescribed_sets",
        {
            "select": (
                "id,workout_exercise_id,set_number,"
                "target_reps,target_weight_kg,"
                "target_percentage,target_rpe,"
                "rest_seconds,notes"
            ),
            "workout_exercise_id":
                f"in.({','.join(workout_exercise_ids)})",
            "order": "set_number.asc"
        }
    )


    # --------------------------------------------------------
    # CREIAMO MAPPE LOCALI
    # Nessuna altra chiamata internet
    # --------------------------------------------------------

    exercises_by_id = {
        exercise["id"]: exercise
        for exercise in exercises
    }

    sets_by_workout_exercise = {}

    for prescribed_set in prescribed_sets:

        we_id = prescribed_set["workout_exercise_id"]

        if we_id not in sets_by_workout_exercise:
            sets_by_workout_exercise[we_id] = []

        sets_by_workout_exercise[we_id].append(
            prescribed_set
        )


    # --------------------------------------------------------
    # DATI FINALI
    # --------------------------------------------------------

    exercise_data = []

    for we in workout_exercises:

        exercise = exercises_by_id.get(
            we["exercise_id"]
        )

        if not exercise:
            continue

        exercise_data.append(
            {
                "workout_exercise": we,
                "exercise": exercise,
                "sets":
                    sets_by_workout_exercise.get(
                        we["id"],
                        []
                    )
            }
        )


    return {
        "athlete": athlete,
        "program": program,
        "workout": workout,
        "exercises": exercise_data
    }


# ============================================================
# CSS TEMPORANEO
# IL DESIGN LO RIFAREMO
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
    }

    .hello {
        font-size: 32px;
        font-weight: 900;
        margin-top: 4px;
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
        margin: 15px 0 20px 0;
    }

    .tag {
        color: #ff4b4f;
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 1px;
    }

    .workout-title {
        color: white;
        font-size: 28px;
        font-weight: 900;
        margin-top: 4px;
    }

    .workout-info {
        color: #a1a6af;
        margin-top: 5px;
    }

    .exercise-card {
        background: #14171c;
        border: 1px solid #292d34;
        border-radius: 16px;
        padding: 18px;
        margin-top: 18px;
    }

    .exercise-number {
        color: #ff4b4f;
        font-size: 11px;
        font-weight: 800;
    }

    .exercise-title {
        font-size: 22px;
        font-weight: 800;
    }

    .exercise-category {
        color: #979ca5;
        font-size: 14px;
    }

    .prescription {
        background: #101216;
        border: 1px solid #242830;
        border-radius: 10px;
        padding: 11px 14px;
        margin-top: 10px;
    }

    div.stButton > button {
        width: 100%;
        min-height: 50px;
        border-radius: 12px;
        border: none;
        background: #e63236;
        color: white;
        font-weight: 800;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# LOAD
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
# HOME
# ============================================================

st.markdown(
    '<div class="brand">TRAINING HUB</div>',
    unsafe_allow_html=True
)

st.markdown(
    f'<div class="hello">'
    f'Ciao, {athlete["first_name"]} 👋'
    f'</div>',
    unsafe_allow_html=True
)

st.markdown(
    f'<div class="subtitle">'
    f'{program["name"]}'
    f'</div>',
    unsafe_allow_html=True
)


exercise_count = len(exercise_data)

exercise_word = (
    "esercizio"
    if exercise_count == 1
    else "esercizi"
)

minutes = (
    workout.get("estimated_minutes")
    or "--"
)


card = (
    '<div class="workout-card">'
    '<div class="tag">ALLENAMENTO</div>'
    f'<div class="workout-title">'
    f'{workout["name"]}'
    f'</div>'
    '<div class="workout-info">'
    f'{exercise_count} {exercise_word}'
    f' &nbsp; • &nbsp; circa {minutes} min'
    '</div>'
    '</div>'
)

st.markdown(
    card,
    unsafe_allow_html=True
)


# ============================================================
# START
# ============================================================

if st.button(
    "▶ INIZIA ALLENAMENTO",
    key="start"
):

    st.session_state["training_started"] = True


# ============================================================
# WORKOUT
# ============================================================

if st.session_state.get(
    "training_started",
    False
):

    st.markdown("## Allenamento")

    for index, item in enumerate(
        exercise_data,
        start=1
    ):

        exercise = item["exercise"]
        we = item["workout_exercise"]
        sets = item["sets"]


        # ----------------------------------------------------
        # CARD ESERCIZIO
        # ----------------------------------------------------

        exercise_card = (
            '<div class="exercise-card">'
            f'<div class="exercise-number">'
            f'ESERCIZIO {index}'
            f'</div>'
            f'<div class="exercise-title">'
            f'{exercise["name"]}'
            f'</div>'
            f'<div class="exercise-category">'
            f'{exercise.get("category") or ""}'
            f'</div>'
            '</div>'
        )

        st.markdown(
            exercise_card,
            unsafe_allow_html=True
        )


        # ----------------------------------------------------
        # FOTO
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
                f"📝 {we['coach_notes']}"
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
        # SERIE
        # ----------------------------------------------------

        for prescribed_set in sets:

            set_number = (
                prescribed_set["set_number"]
            )

            reps = (
                prescribed_set.get(
                    "target_reps"
                )
            )

            weight = (
                prescribed_set.get(
                    "target_weight_kg"
                )
            )


            prescription = (
                '<div class="prescription">'
                f'<b>Serie {set_number}</b><br>'
                f'Prescritto: '
                f'{reps if reps is not None else "-"} reps'
                f' × '
                f'{weight if weight is not None else "-"} kg'
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
                    value=float(
                        weight or 0
                    ),
                    step=2.5,
                    key=(
                        f"kg_"
                        f"{we['id']}_"
                        f"{set_number}"
                    )
                )


            with col2:

                st.number_input(
                    "Reps fatte",
                    min_value=0,
                    value=int(
                        reps or 0
                    ),
                    step=1,
                    key=(
                        f"reps_"
                        f"{we['id']}_"
                        f"{set_number}"
                    )
                )


        # ----------------------------------------------------
        # EXTRA SET
        # ----------------------------------------------------

        extra_key = (
            f"extra_sets_{we['id']}"
        )

        if extra_key not in st.session_state:

            st.session_state[
                extra_key
            ] = 0


        if st.button(
            "＋ AGGIUNGI SERIE",
            key=f"extra_button_{we['id']}"
        ):

            st.session_state[
                extra_key
            ] += 1


        for extra_index in range(
            st.session_state[extra_key]
        ):

            st.markdown(
                f"#### Serie extra "
                f"{extra_index + 1}"
            )

            col1, col2 = st.columns(2)

            with col1:

                st.number_input(
                    "KG",
                    min_value=0.0,
                    step=2.5,
                    key=(
                        f"extra_kg_"
                        f"{we['id']}_"
                        f"{extra_index}"
                    )
                )

            with col2:

                st.number_input(
                    "Reps",
                    min_value=0,
                    step=1,
                    key=(
                        f"extra_reps_"
                        f"{we['id']}_"
                        f"{extra_index}"
                    )
                )


        st.markdown("---")


    # ========================================================
    # SESSIONE
    # ========================================================

    st.markdown("## Fine allenamento")

    st.slider(
        "RPE sessione",
        min_value=1,
        max_value=10,
        value=7,
        key="session_rpe"
    )

    st.text_area(
        "Note allenamento",
        placeholder=(
            "Come è andato "
            "l'allenamento?"
        ),
        key="athlete_notes"
    )

    if st.button(
        "✓ COMPLETA ALLENAMENTO",
        key="complete"
    ):

        st.success(
            "Allenamento pronto "
            "per essere salvato! 💪"
        )
