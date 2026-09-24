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


@st.cache_data(ttl=300)
def load_training():

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

    workouts = supabase_get(
        "workouts",
        {
            "select": "id,name,description,estimated_minutes,week_number,day_number,workout_order",
            "program_id": f"eq.{program_id}",
            "order": "workout_order.asc",
            "limit": "1"
        }
    )

    if not workouts:
        return None

    workout = workouts[0]

    # --------------------------------------------------------
    # BLOCCHI
    # --------------------------------------------------------

    blocks = supabase_get(
        "workout_blocks",
        {
            "select": "id,name,block_type,block_order,description",
            "workout_id": f"eq.{workout['id']}",
            "order": "block_order.asc"
        }
    )

    # --------------------------------------------------------
    # WORKOUT EXERCISES
    # --------------------------------------------------------

    workout_exercises = supabase_get(
        "workout_exercises",
        {
            "select": (
                "id,exercise_id,exercise_order,"
                "default_rest_seconds,coach_notes,"
                "block_id,exercise_code,group_code,alternating"
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
            "blocks": blocks,
            "exercises": []
        }

    exercise_ids = [str(x["exercise_id"]) for x in workout_exercises]

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

    workout_exercise_ids = [str(x["id"]) for x in workout_exercises]

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

    exercises_by_id = {x["id"]: x for x in exercises}

    sets_by_we = {}

    for prescribed_set in prescribed_sets:

        we_id = prescribed_set["workout_exercise_id"]

        if we_id not in sets_by_we:
            sets_by_we[we_id] = []

        sets_by_we[we_id].append(prescribed_set)

    exercise_data = []

    for we in workout_exercises:

        exercise = exercises_by_id.get(we["exercise_id"])

        if not exercise:
            continue

        exercise_data.append({
            "workout_exercise": we,
            "exercise": exercise,
            "sets": sets_by_we.get(we["id"], [])
        })

    return {
        "athlete": athlete,
        "program": program,
        "workout": workout,
        "blocks": blocks,
        "exercises": exercise_data
    }


# ============================================================
# LOAD
# ============================================================

try:
    DATA = load_training()

except Exception as e:
    st.error(f"Errore collegamento database: {e}")
    st.stop()


if not DATA:
    st.error("Nessun programma trovato.")
    st.stop()


# ============================================================
# SESSION STATE
# ============================================================

if "screen" not in st.session_state:
    st.session_state.screen = "home"

if "selected_exercise" not in st.session_state:
    st.session_state.selected_exercise = None

if "training_started" not in st.session_state:
    st.session_state.training_started = False


# ============================================================
# CSS
# ============================================================

st.markdown("""
<style>

/* ----------------------------------------------------------
   STREAMLIT RESET
---------------------------------------------------------- */

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

header {
    visibility: hidden;
}

[data-testid="stToolbar"] {
    display: none;
}

[data-testid="stDecoration"] {
    display: none;
}

[data-testid="stStatusWidget"] {
    display: none;
}

.block-container {
    max-width: 620px;
    padding-top: 18px;
    padding-bottom: 110px;
    padding-left: 16px;
    padding-right: 16px;
}

.stApp {
    background:
        radial-gradient(
            circle at top,
            #191d24 0%,
            #0b0d10 42%,
            #070809 100%
        );
    color: #ffffff;
}


/* ----------------------------------------------------------
   TYPOGRAPHY
---------------------------------------------------------- */

html, body, [class*="css"] {
    font-family:
        Inter,
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
}

h1, h2, h3 {
    color: #ffffff !important;
}


/* ----------------------------------------------------------
   LOGO / HEADER
---------------------------------------------------------- */

.app-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 26px;
}

.logo {
    font-size: 19px;
    font-weight: 900;
    letter-spacing: 1px;
}

.logo-red {
    color: #ff3b43;
}

.avatar {
    width: 38px;
    height: 38px;
    border-radius: 50%;
    background: #1d2128;
    border: 1px solid #30353e;
    display: flex;
    justify-content: center;
    align-items: center;
    font-weight: 800;
}


/* ----------------------------------------------------------
   HOME
---------------------------------------------------------- */

.hello {
    font-size: 29px;
    line-height: 1.1;
    font-weight: 900;
    margin-bottom: 5px;
}

.program-name {
    color: #9097a3;
    font-size: 14px;
    margin-bottom: 24px;
}


/* ----------------------------------------------------------
   HERO WORKOUT
---------------------------------------------------------- */

.hero {
    background:
        linear-gradient(
            145deg,
            #20242b,
            #12151a
        );
    border: 1px solid #30343c;
    border-radius: 24px;
    padding: 22px;
    margin-bottom: 14px;
    box-shadow:
        0 18px 45px rgba(0,0,0,.30);
}

.hero-label {
    color: #ff4a50;
    font-size: 12px;
    font-weight: 900;
    letter-spacing: 1.4px;
}

.hero-title {
    font-size: 30px;
    font-weight: 900;
    margin-top: 5px;
    margin-bottom: 4px;
}

.hero-sub {
    color: #9ca3ad;
    font-size: 14px;
}

.stats {
    display: flex;
    gap: 8px;
    margin-top: 22px;
}

.stat {
    flex: 1;
    background: #0d0f12;
    border-radius: 13px;
    padding: 12px 8px;
    text-align: center;
}

.stat-number {
    font-size: 18px;
    font-weight: 900;
}

.stat-label {
    color: #747b85;
    font-size: 10px;
    margin-top: 2px;
    text-transform: uppercase;
}


/* ----------------------------------------------------------
   PROGRESS
---------------------------------------------------------- */

.progress-bg {
    width: 100%;
    height: 7px;
    background: #272b31;
    border-radius: 100px;
    overflow: hidden;
    margin-top: 15px;
}

.progress-fill {
    height: 7px;
    background:
        linear-gradient(
            90deg,
            #ff3038,
            #ff656a
        );
    border-radius: 100px;
}


/* ----------------------------------------------------------
   SECTION
---------------------------------------------------------- */

.section-title {
    color: #8b929d;
    font-size: 11px;
    font-weight: 900;
    letter-spacing: 1.5px;
    margin-top: 27px;
    margin-bottom: 10px;
    text-transform: uppercase;
}


/* ----------------------------------------------------------
   EXERCISE CARD
---------------------------------------------------------- */

.exercise-card {
    background: #14171c;
    border: 1px solid #292d34;
    border-radius: 17px;
    padding: 13px;
    margin-bottom: 7px;
}

.exercise-row {
    display: flex;
    align-items: center;
    gap: 13px;
}

.exercise-img {
    width: 72px;
    height: 72px;
    min-width: 72px;
    border-radius: 13px;
    background: #22262c;
    object-fit: cover;
}

.exercise-placeholder {
    width: 72px;
    height: 72px;
    min-width: 72px;
    border-radius: 13px;
    background:
        linear-gradient(
            145deg,
            #252a31,
            #171a1f
        );
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 27px;
}

.exercise-info {
    flex: 1;
}

.exercise-code {
    color: #ff4a50;
    font-size: 11px;
    font-weight: 900;
}

.exercise-name {
    color: #ffffff;
    font-size: 16px;
    font-weight: 850;
    margin-top: 2px;
}

.exercise-prescription {
    color: #a2a8b1;
    font-size: 12px;
    margin-top: 5px;
}

.exercise-progress {
    color: #737b86;
    font-size: 11px;
    margin-top: 4px;
}


/* ----------------------------------------------------------
   STATUS
---------------------------------------------------------- */

.status-todo {
    color: #858c96;
}

.status-active {
    color: #ff5056;
    font-weight: 800;
}

.status-done {
    color: #4bd486;
    font-weight: 800;
}


/* ----------------------------------------------------------
   EXERCISE DETAIL
---------------------------------------------------------- */

.detail-code {
    color: #ff4a50;
    font-weight: 900;
    font-size: 12px;
    letter-spacing: 1px;
}

.detail-name {
    font-size: 29px;
    font-weight: 900;
    line-height: 1.08;
    margin-top: 3px;
}

.detail-category {
    color: #8f96a0;
    font-size: 13px;
    margin-top: 5px;
}

.media-placeholder {
    width: 100%;
    height: 190px;
    border-radius: 20px;
    background:
        linear-gradient(
            145deg,
            #242930,
            #111419
        );
    display: flex;
    align-items: center;
    justify-content: center;
    margin-top: 18px;
    font-size: 45px;
    color: #555d68;
}


/* ----------------------------------------------------------
   PRESCRIPTION
---------------------------------------------------------- */

.set-header {
    display: grid;
    grid-template-columns: 45px 1fr 1fr 42px;
    gap: 6px;
    color: #717985;
    font-size: 10px;
    font-weight: 800;
    text-transform: uppercase;
    margin-top: 22px;
    margin-bottom: 7px;
    padding: 0 4px;
}

.set-prescribed {
    color: #a8afb8;
    font-size: 12px;
}


/* ----------------------------------------------------------
   NOTES
---------------------------------------------------------- */

.coach-note {
    background: #171b21;
    border-left: 3px solid #ff4148;
    border-radius: 12px;
    padding: 13px;
    color: #aeb4bc;
    font-size: 13px;
    margin-top: 15px;
}


/* ----------------------------------------------------------
   STREAMLIT BUTTONS
---------------------------------------------------------- */

.stButton > button {
    width: 100%;
    min-height: 45px;
    border-radius: 13px;
    border: 1px solid #32363d;
    background: #181b20;
    color: #ffffff;
    font-weight: 750;
}

.stButton > button:hover {
    border-color: #ff4148;
    color: #ffffff;
}

div[data-testid="stFormSubmitButton"] > button {
    background: #ff343c;
    border: none;
}


/* ----------------------------------------------------------
   INPUT
---------------------------------------------------------- */

[data-testid="stNumberInput"] input {
    text-align: center;
    font-weight: 800;
}

[data-testid="stNumberInput"] {
    margin-bottom: 0px;
}


/* ----------------------------------------------------------
   BOTTOM NAV
---------------------------------------------------------- */

.bottom-space {
    height: 20px;
}

.nav {
    position: fixed;
    bottom: 0;
    left: 50%;
    transform: translateX(-50%);
    width: min(620px, 100%);
    height: 70px;
    background: rgba(12,14,17,.97);
    border-top: 1px solid #272b31;
    backdrop-filter: blur(16px);
    z-index: 999;
    display: flex;
    justify-content: space-around;
    align-items: center;
}

.nav-item {
    text-align: center;
    color: #737b85;
    font-size: 10px;
    font-weight: 700;
}

.nav-icon {
    font-size: 20px;
    margin-bottom: 2px;
}

.nav-active {
    color: #ff464d;
}


/* ----------------------------------------------------------
   MOBILE
---------------------------------------------------------- */

@media (max-width: 600px) {

    .block-container {
        padding-left: 13px;
        padding-right: 13px;
        padding-top: 12px;
    }

    .hello {
        font-size: 26px;
    }

    .hero-title {
        font-size: 27px;
    }

    .exercise-img,
    .exercise-placeholder {
        width: 65px;
        height: 65px;
        min-width: 65px;
    }

}

</style>
""", unsafe_allow_html=True)


# ============================================================
# HELPERS
# ============================================================

def go(screen):
    st.session_state.screen = screen
    st.rerun()


def format_weight(value):

    if value is None:
        return ""

    value = float(value)

    if value.is_integer():
        return str(int(value))

    return str(value)


def prescription_text(sets):

    if not sets:
        return "Serie non impostate"

    pieces = []

    for s in sets:

        reps = s.get("target_reps")
        weight = s.get("target_weight_kg")

        if reps is not None and weight is not None:
            pieces.append(
                f"{reps}×{format_weight(weight)}kg"
            )

        elif reps is not None:
            pieces.append(f"{reps} reps")

        elif weight is not None:
            pieces.append(
                f"{format_weight(weight)}kg"
            )

    # se sono tutte uguali, mostriamo 3 × 10
    if pieces and len(set(pieces)) == 1:

        first = sets[0]

        reps = first.get("target_reps")
        weight = first.get("target_weight_kg")

        if reps is not None and weight is None:
            return f"{len(sets)} × {reps}"

        if reps is not None and weight is not None:
            return (
                f"{len(sets)} × "
                f"{reps} @ {format_weight(weight)} kg"
            )

    return " • ".join(pieces)


def get_set_key(we_id, set_number, field):
    return f"we_{we_id}_set_{set_number}_{field}"


def completed_sets(item):

    we_id = item["workout_exercise"]["id"]

    completed = 0

    for s in item["sets"]:

        key = get_set_key(
            we_id,
            s["set_number"],
            "done"
        )

        if st.session_state.get(key, False):
            completed += 1

    extra_count = st.session_state.get(
        f"extra_count_{we_id}",
        0
    )

    for i in range(extra_count):

        key = get_set_key(
            we_id,
            f"extra_{i}",
            "done"
        )

        if st.session_state.get(key, False):
            completed += 1

    return completed


def total_sets(item):

    we_id = item["workout_exercise"]["id"]

    return (
        len(item["sets"])
        +
        st.session_state.get(
            f"extra_count_{we_id}",
            0
        )
    )


def exercise_status(item):

    completed = completed_sets(item)
    total = total_sets(item)

    if total > 0 and completed >= total:
        return "done"

    if completed > 0:
        return "active"

    return "todo"


def total_progress():

    total = 0
    completed = 0

    for item in DATA["exercises"]:
        total += total_sets(item)
        completed += completed_sets(item)

    if total == 0:
        return 0

    return int((completed / total) * 100)


def find_exercise(we_id):

    for item in DATA["exercises"]:

        if item["workout_exercise"]["id"] == we_id:
            return item

    return None


def open_exercise(we_id):

    st.session_state.selected_exercise = we_id
    st.session_state.screen = "exercise"
    st.session_state.training_started = True
    st.rerun()


def bottom_nav(active="today"):

    items = [
        ("⌂", "Oggi", "today"),
        ("▤", "Programma", "program"),
        ("▥", "Progressi", "progress"),
        ("○", "Profilo", "profile")
    ]

    html = '<div class="nav">'

    for icon, label, key in items:

        active_class = (
            "nav-active"
            if key == active
            else ""
        )

        html += f"""
        <div class="nav-item {active_class}">
            <div class="nav-icon">{icon}</div>
            <div>{label}</div>
        </div>
        """

    html += "</div>"

    st.markdown(
        html,
        unsafe_allow_html=True
    )


# ============================================================
# HOME
# ============================================================

def render_home():

    athlete = DATA["athlete"]
    workout = DATA["workout"]
    program = DATA["program"]

    first_letter = (
        athlete.get("first_name", "A")[0].upper()
    )

    st.markdown(
        f"""
        <div class="app-top">
            <div class="logo">
                TRAINING <span class="logo-red">HUB</span>
            </div>
            <div class="avatar">
                {first_letter}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <div class="hello">
            Ciao, {athlete['first_name']} 👋
        </div>

        <div class="program-name">
            {program['name']}
        </div>
        """,
        unsafe_allow_html=True
    )

    progress = total_progress()

    exercise_count = len(DATA["exercises"])
    block_count = len(DATA["blocks"])

    minutes = (
        workout.get("estimated_minutes")
        or "—"
    )

    st.markdown(
        f"""
        <div class="hero">

            <div class="hero-label">
                ALLENAMENTO DI OGGI
            </div>

            <div class="hero-title">
                {workout['name']}
            </div>

            <div class="hero-sub">
                La tua sessione è pronta.
            </div>

            <div class="stats">

                <div class="stat">
                    <div class="stat-number">
                        {exercise_count}
                    </div>
                    <div class="stat-label">
                        Esercizi
                    </div>
                </div>

                <div class="stat">
                    <div class="stat-number">
                        {minutes}'
                    </div>
                    <div class="stat-label">
                        Durata
                    </div>
                </div>

                <div class="stat">
                    <div class="stat-number">
                        {block_count}
                    </div>
                    <div class="stat-label">
                        Blocchi
                    </div>
                </div>

            </div>

            <div class="progress-bg">
                <div
                    class="progress-fill"
                    style="width:{progress}%;">
                </div>
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    label = (
        "CONTINUA ALLENAMENTO"
        if st.session_state.training_started
        else "▶ INIZIA ALLENAMENTO"
    )

    if st.button(
        label,
        type="primary",
        use_container_width=True
    ):
        st.session_state.training_started = True
        go("workout")

    st.markdown(
        '<div class="section-title">IL TUO PROGRAMMA</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <div class="exercise-card">
            <div class="exercise-name">
                {program['name']}
            </div>
            <div class="exercise-prescription">
                Visualizza scheda, esercizi e progressi
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    bottom_nav("today")


# ============================================================
# WORKOUT OVERVIEW
# ============================================================

def render_workout():

    workout = DATA["workout"]
    progress = total_progress()

    top_left, top_right = st.columns(
        [1, 4]
    )

    with top_left:
        if st.button("‹", key="back_home"):
            go("home")

    with top_right:
        st.markdown(
            f"""
            <div style="
                font-size:22px;
                font-weight:900;
                padding-top:7px;
            ">
                {workout['name']}
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown(
        f"""
        <div style="
            display:flex;
            justify-content:space-between;
            color:#858c96;
            font-size:12px;
            margin-top:8px;
        ">
            <span>
                {len(DATA['exercises'])} esercizi
            </span>
            <span>
                {progress}% completato
            </span>
        </div>

        <div class="progress-bg">
            <div
                class="progress-fill"
                style="width:{progress}%;">
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    blocks_by_id = {
        block["id"]: block
        for block in DATA["blocks"]
    }

    grouped = {}

    for item in DATA["exercises"]:

        block_id = (
            item["workout_exercise"]
            .get("block_id")
        )

        if block_id not in grouped:
            grouped[block_id] = []

        grouped[block_id].append(item)

    # BLOCCHI IN ORDINE
    for block in DATA["blocks"]:

        items = grouped.get(
            block["id"],
            []
        )

        if not items:
            continue

        st.markdown(
            f"""
            <div class="section-title">
                {block['name']}
            </div>
            """,
            unsafe_allow_html=True
        )

        for item in items:

            exercise = item["exercise"]
            we = item["workout_exercise"]

            done = completed_sets(item)
            total = total_sets(item)

            status = exercise_status(item)

            if status == "done":
                status_html = (
                    '<span class="status-done">'
                    '✓ COMPLETATO</span>'
                )

            elif status == "active":
                status_html = (
                    '<span class="status-active">'
                    '● IN CORSO</span>'
                )

            else:
                status_html = (
                    '<span class="status-todo">'
                    '○ DA FARE</span>'
                )

            code = (
                we.get("exercise_code")
                or ""
            )

            image_url = exercise.get(
                "image_url"
            )

            if image_url:

                image_html = f"""
                <img
                    class="exercise-img"
                    src="{image_url}">
                """

            else:

                image_html = """
                <div class="exercise-placeholder">
                    🏋️
                </div>
                """

            prescription = prescription_text(
                item["sets"]
            )

            rest = (
                we.get(
                    "default_rest_seconds"
                )
                or "—"
            )

            st.markdown(
                f"""
                <div class="exercise-card">
                    <div class="exercise-row">

                        {image_html}

                        <div class="exercise-info">

                            <div class="exercise-code">
                                {code}
                            </div>

                            <div class="exercise-name">
                                {exercise['name']}
                            </div>

                            <div class="exercise-prescription">
                                {prescription}
                            </div>

                            <div class="exercise-progress">
                                {done}/{total} serie
                                &nbsp;•&nbsp;
                                ⏱ {rest}"
                                &nbsp;•&nbsp;
                                {status_html}
                            </div>

                        </div>

                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            if st.button(
                f"APRI {exercise['name'].upper()}  ›",
                key=f"open_{we['id']}"
            ):
                open_exercise(we["id"])

    # eventuali esercizi senza blocco
    ungrouped = grouped.get(None, [])

    if ungrouped:

        st.markdown(
            """
            <div class="section-title">
                ALTRI ESERCIZI
            </div>
            """,
            unsafe_allow_html=True
        )

        for item in ungrouped:

            exercise = item["exercise"]
            we = item["workout_exercise"]

            if st.button(
                exercise["name"],
                key=f"open_other_{we['id']}"
            ):
                open_exercise(we["id"])

    st.markdown(
        '<div class="bottom-space"></div>',
        unsafe_allow_html=True
    )

    bottom_nav("today")


# ============================================================
# EXERCISE DETAIL
# ============================================================

def render_exercise():

    we_id = st.session_state.selected_exercise

    item = find_exercise(we_id)

    if not item:
        go("workout")
        return

    exercise = item["exercise"]
    we = item["workout_exercise"]
    sets = item["sets"]

    # BACK
    if st.button(
        "‹  TUTTI GLI ESERCIZI",
        key="back_workout"
    ):
        go("workout")

    code = we.get("exercise_code") or ""

    st.markdown(
        f"""
        <div class="detail-code">
            {code}
        </div>

        <div class="detail-name">
            {exercise['name']}
        </div>

        <div class="detail-category">
            {exercise.get('category') or ''}
        </div>
        """,
        unsafe_allow_html=True
    )

    # MEDIA
    if exercise.get("image_url"):

        st.image(
            exercise["image_url"],
            use_container_width=True
        )

    else:

        st.markdown(
            """
            <div class="media-placeholder">
                🏋️
            </div>
            """,
            unsafe_allow_html=True
        )

    if exercise.get("video_url"):

        st.link_button(
            "▶ GUARDA VIDEO",
            exercise["video_url"],
            use_container_width=True
        )

    if exercise.get("description"):

        st.caption(
            exercise["description"]
        )

    # COACH NOTE
    if we.get("coach_notes"):

        st.markdown(
            f"""
            <div class="coach-note">
                <strong>NOTA COACH</strong><br>
                {we['coach_notes']}
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown(
        """
        <div class="section-title">
            SERIE
        </div>
        """,
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # PRESCRIBED SETS
    # --------------------------------------------------------

    for prescribed_set in sets:

        set_number = prescribed_set[
            "set_number"
        ]

        target_reps = (
            prescribed_set.get(
                "target_reps"
            )
            or 0
        )

        target_weight = (
            prescribed_set.get(
                "target_weight_kg"
            )
        )

        weight_default = (
            float(target_weight)
            if target_weight is not None
            else 0.0
        )

        kg_key = get_set_key(
            we_id,
            set_number,
            "kg"
        )

        reps_key = get_set_key(
            we_id,
            set_number,
            "reps"
        )

        done_key = get_set_key(
            we_id,
            set_number,
            "done"
        )

        if kg_key not in st.session_state:
            st.session_state[kg_key] = weight_default

        if reps_key not in st.session_state:
            st.session_state[reps_key] = int(
                target_reps
            )

        prescribed = ""

        if target_reps:
            prescribed += f"{target_reps}"

        if target_weight is not None:
            prescribed += (
                f" × "
                f"{format_weight(target_weight)} kg"
            )
        else:
            prescribed += " reps"

        st.markdown(
            f"""
            <div style="
                color:#8b929d;
                font-size:11px;
                margin-top:10px;
                margin-bottom:4px;
            ">
                SERIE {set_number}
                &nbsp; • &nbsp;
                PRESCRITTO:
                <strong style="color:white;">
                    {prescribed}
                </strong>
            </div>
            """,
            unsafe_allow_html=True
        )

        c1, c2, c3 = st.columns(
            [1, 1, .35]
        )

        with c1:

            st.number_input(
                "KG",
                min_value=0.0,
                step=2.5,
                key=kg_key
            )

        with c2:

            st.number_input(
                "REPS",
                min_value=0,
                step=1,
                key=reps_key
            )

        with c3:

            st.write("")
            st.checkbox(
                "✓",
                key=done_key,
                label_visibility="collapsed"
            )

    # --------------------------------------------------------
    # EXTRA SETS
    # --------------------------------------------------------

    extra_key = f"extra_count_{we_id}"

    if extra_key not in st.session_state:
        st.session_state[extra_key] = 0

    for i in range(
        st.session_state[extra_key]
    ):

        number = i + 1

        kg_key = get_set_key(
            we_id,
            f"extra_{i}",
            "kg"
        )

        reps_key = get_set_key(
            we_id,
            f"extra_{i}",
            "reps"
        )

        done_key = get_set_key(
            we_id,
            f"extra_{i}",
            "done"
        )

        st.markdown(
            f"""
            <div style="
                color:#ff555b;
                font-size:11px;
                font-weight:800;
                margin-top:13px;
            ">
                SERIE EXTRA {number}
            </div>
            """,
            unsafe_allow_html=True
        )

        c1, c2, c3 = st.columns(
            [1, 1, .35]
        )

        with c1:

            st.number_input(
                "KG",
                min_value=0.0,
                step=2.5,
                key=kg_key
            )

        with c2:

            st.number_input(
                "REPS",
                min_value=0,
                step=1,
                key=reps_key
            )

        with c3:

            st.write("")
            st.checkbox(
                "✓",
                key=done_key,
                label_visibility="collapsed"
            )

    if st.button(
        "＋ AGGIUNGI SERIE",
        key=f"add_set_{we_id}"
    ):

        st.session_state[extra_key] += 1
        st.rerun()

    # --------------------------------------------------------
    # REST
    # --------------------------------------------------------

    rest = (
        we.get("default_rest_seconds")
        or 0
    )

    if rest:

        minutes = rest // 60
        seconds = rest % 60

        st.markdown(
            f"""
            <div style="
                margin-top:17px;
                background:#15181d;
                border:1px solid #292d34;
                border-radius:15px;
                padding:14px;
                display:flex;
                justify-content:space-between;
                align-items:center;
            ">
                <span style="
                    color:#8d949e;
                    font-size:12px;
                    font-weight:800;
                ">
                    ⏱ RECUPERO
                </span>

                <span style="
                    color:white;
                    font-size:21px;
                    font-weight:900;
                ">
                    {minutes:02d}:{seconds:02d}
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )

    # --------------------------------------------------------
    # NEXT EXERCISE
    # --------------------------------------------------------

    current_index = None

    for i, candidate in enumerate(
        DATA["exercises"]
    ):

        if (
            candidate["workout_exercise"]["id"]
            == we_id
        ):
            current_index = i
            break

    if (
        current_index is not None
        and current_index
        < len(DATA["exercises"]) - 1
    ):

        next_item = DATA["exercises"][
            current_index + 1
        ]

        next_name = (
            next_item["exercise"]["name"]
        )

        next_id = (
            next_item["workout_exercise"]["id"]
        )

        if st.button(
            f"PROSSIMO: {next_name.upper()}  →",
            key=f"next_{we_id}"
        ):
            open_exercise(next_id)

    bottom_nav("today")


# ============================================================
# ROUTER
# ============================================================

if st.session_state.screen == "home":

    render_home()

elif st.session_state.screen == "workout":

    render_workout()

elif st.session_state.screen == "exercise":

    render_exercise()

else:

    st.session_state.screen = "home"
    st.rerun()
