import streamlit as st
import requests
import html

# ============================================================
# TRAINING HUB V3
# Mobile-first
# ============================================================

st.set_page_config(
    page_title="Training Hub",
    page_icon="💪",
    layout="centered",
    initial_sidebar_state="collapsed",
)

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
}


# ============================================================
# SUPABASE
# ============================================================

def supabase_get(table, params=None):
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/{table}",
        headers=HEADERS,
        params=params,
        timeout=10,
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
            "limit": "1",
        },
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
            "limit": "1",
        },
    )

    if not assignments:
        return None

    program_id = assignments[0]["program_id"]

    programs = supabase_get(
        "programs",
        {
            "select": "id,name,description,start_date,end_date",
            "id": f"eq.{program_id}",
            "limit": "1",
        },
    )

    if not programs:
        return None

    program = programs[0]

    workouts = supabase_get(
        "workouts",
        {
            "select": (
                "id,name,description,estimated_minutes,"
                "week_number,day_number,workout_order"
            ),
            "program_id": f"eq.{program_id}",
            "order": "workout_order.asc",
            "limit": "1",
        },
    )

    if not workouts:
        return None

    workout = workouts[0]

    blocks = supabase_get(
        "workout_blocks",
        {
            "select": "id,name,block_type,block_order,description",
            "workout_id": f"eq.{workout['id']}",
            "order": "block_order.asc",
        },
    )

    workout_exercises = supabase_get(
        "workout_exercises",
        {
            "select": (
                "id,exercise_id,exercise_order,"
                "default_rest_seconds,coach_notes,"
                "block_id,exercise_code,group_code,alternating"
            ),
            "workout_id": f"eq.{workout['id']}",
            "order": "exercise_order.asc",
        },
    )

    if not workout_exercises:
        return {
            "athlete": athlete,
            "program": program,
            "workout": workout,
            "blocks": blocks,
            "exercises": [],
        }

    exercise_ids = [
        str(x["exercise_id"])
        for x in workout_exercises
    ]

    exercises = supabase_get(
        "exercises",
        {
            "select": (
                "id,name,category,muscle_group,"
                "description,image_url,video_url"
            ),
            "id": f"in.({','.join(exercise_ids)})",
        },
    )

    workout_exercise_ids = [
        str(x["id"])
        for x in workout_exercises
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
            "workout_exercise_id": (
                f"in.({','.join(workout_exercise_ids)})"
            ),
            "order": "set_number.asc",
        },
    )

    exercises_by_id = {
        x["id"]: x
        for x in exercises
    }

    sets_by_we = {}

    for prescribed_set in prescribed_sets:

        we_id = prescribed_set["workout_exercise_id"]

        sets_by_we.setdefault(
            we_id,
            []
        ).append(prescribed_set)

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
                "sets": sets_by_we.get(
                    we["id"],
                    []
                ),
            }
        )

    return {
        "athlete": athlete,
        "program": program,
        "workout": workout,
        "blocks": blocks,
        "exercises": exercise_data,
    }


# ============================================================
# LOAD
# ============================================================

try:
    DATA = load_training()

except Exception as e:
    st.error(
        f"Errore collegamento database: {e}"
    )
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

st.markdown(
"""
<style>

/* =========================================================
   STREAMLIT RESET
========================================================= */

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

header {
    visibility: hidden;
}

[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"] {
    display: none;
}

.stApp {
    background:
        radial-gradient(
            circle at top,
            #191d23 0%,
            #0d0f12 38%,
            #070809 100%
        );
    color: white;
}

.block-container {
    max-width: 620px;
    padding-top: 18px;
    padding-left: 16px;
    padding-right: 16px;
    padding-bottom: 105px;
}

html,
body,
[class*="css"] {
    font-family:
        Inter,
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
}


/* =========================================================
   HEADER
========================================================= */

.app-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 28px;
}

.logo {
    color: white;
    font-size: 18px;
    font-weight: 900;
    letter-spacing: 1px;
}

.logo-red {
    color: #ff3b43;
}

.avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;

    background: #20242a;
    border: 1px solid #343942;

    display: flex;
    align-items: center;
    justify-content: center;

    font-weight: 900;
}


/* =========================================================
   HOME
========================================================= */

.hello {
    font-size: 30px;
    font-weight: 900;
    line-height: 1.1;
}

.program-name {
    margin-top: 7px;
    margin-bottom: 25px;

    color: #9299a4;
    font-size: 14px;
}


/* =========================================================
   HERO
========================================================= */

.hero {
    padding: 22px;

    border-radius: 24px;
    border: 1px solid #30343c;

    background:
        linear-gradient(
            145deg,
            #20242b,
            #12151a
        );

    box-shadow:
        0 20px 45px
        rgba(0,0,0,.28);

    margin-bottom: 13px;
}

.hero-label {
    color: #ff4b52;
    font-size: 11px;
    font-weight: 900;
    letter-spacing: 1.4px;
}

.hero-title {
    color: white;
    font-size: 31px;
    font-weight: 900;
    margin-top: 5px;
}

.hero-sub {
    color: #949ba5;
    font-size: 13px;
    margin-top: 2px;
}

.stats {
    display: flex;
    gap: 8px;
    margin-top: 22px;
}

.stat {
    flex: 1;
    padding: 12px 6px;
    border-radius: 14px;
    background: #0c0e11;
    text-align: center;
}

.stat-number {
    color: white;
    font-size: 19px;
    font-weight: 900;
}

.stat-label {
    color: #717985;
    font-size: 9px;
    font-weight: 700;
    text-transform: uppercase;
    margin-top: 2px;
}


/* =========================================================
   PROGRESS
========================================================= */

.progress-bg {
    width: 100%;
    height: 7px;
    margin-top: 17px;

    background: #292d33;
    border-radius: 100px;
    overflow: hidden;
}

.progress-fill {
    height: 100%;
    border-radius: 100px;

    background:
        linear-gradient(
            90deg,
            #ff3039,
            #ff676c
        );
}


/* =========================================================
   SECTION
========================================================= */

.section-title {
    color: #858c97;
    font-size: 11px;
    font-weight: 900;
    letter-spacing: 1.4px;
    text-transform: uppercase;

    margin-top: 27px;
    margin-bottom: 10px;
}


/* =========================================================
   CLICKABLE EXERCISE CARD
========================================================= */

/*
La card viene realizzata usando direttamente
il bottone Streamlit, così TUTTA la superficie
è realmente cliccabile anche su smartphone.
*/

div[data-testid="stButton"] button.exercise-button {
    display: none;
}

.exercise-visual {
    display: flex;
    align-items: center;
    gap: 12px;

    width: 100%;

    padding: 11px;

    border: 1px solid #292e35;
    border-radius: 17px;

    background: #14171c;

    margin-bottom: 0px;

    min-height: 86px;
}

.exercise-thumb {
    width: 64px;
    height: 64px;

    min-width: 64px;

    border-radius: 13px;

    background:
        linear-gradient(
            145deg,
            #292e35,
            #181b20
        );

    display: flex;
    align-items: center;
    justify-content: center;

    overflow: hidden;

    font-size: 25px;
}

.exercise-thumb img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.exercise-info {
    flex: 1;
    min-width: 0;
}

.exercise-code {
    color: #ff4c53;
    font-size: 10px;
    font-weight: 900;
}

.exercise-name {
    color: white;
    font-size: 16px;
    font-weight: 850;
    margin-top: 2px;
}

.exercise-prescription {
    color: #a3a9b1;
    font-size: 12px;
    margin-top: 4px;
    line-height: 1.3;
}

.exercise-progress {
    color: #747c87;
    font-size: 10px;
    margin-top: 4px;
}

.exercise-chevron {
    color: #777f8a;
    font-size: 28px;
    font-weight: 300;
    padding-right: 3px;
}


/* =========================================================
   CARD BUTTON OVERLAY
========================================================= */

.exercise-click-wrap {
    position: relative;
    margin-bottom: 9px;
}

/*
Il vero pulsante Streamlit è posizionato
subito dopo la card. Gli diamo look minimal.
*/

.exercise-open-button button {
    margin-top: -94px !important;
    height: 86px !important;
    opacity: 0.01 !important;
    position: relative !important;
    z-index: 10 !important;
    border-radius: 17px !important;
    cursor: pointer !important;
}

.exercise-open-button {
    height: 0px;
    margin-bottom: 9px;
}


/* =========================================================
   STATUS
========================================================= */

.status-todo {
    color: #858c96;
}

.status-active {
    color: #ff5359;
    font-weight: 800;
}

.status-done {
    color: #4bd486;
    font-weight: 800;
}


/* =========================================================
   EXERCISE DETAIL
========================================================= */

.detail-code {
    color: #ff4a50;
    font-size: 11px;
    font-weight: 900;
    letter-spacing: 1px;
    margin-top: 12px;
}

.detail-name {
    color: white;
    font-size: 30px;
    font-weight: 900;
    line-height: 1.08;
    margin-top: 4px;
}

.detail-category {
    color: #858d98;
    font-size: 13px;
    margin-top: 5px;
}

.media-placeholder {
    width: 100%;
    height: 135px;

    margin-top: 16px;

    border-radius: 18px;

    display: flex;
    align-items: center;
    justify-content: center;

    background:
        linear-gradient(
            145deg,
            #252a31,
            #111419
        );

    color: #565e69;
    font-size: 36px;
}


/* =========================================================
   COACH NOTE
========================================================= */

.coach-note {
    margin-top: 13px;
    padding: 12px;

    border-radius: 12px;
    border-left: 3px solid #ff4148;

    background: #171b20;

    color: #abb1ba;
    font-size: 12px;
    line-height: 1.45;
}

.coach-note-title {
    color: white;
    font-weight: 900;
    font-size: 10px;
    letter-spacing: 1px;
}


/* =========================================================
   SETS - MOBILE FIRST
========================================================= */

.set-head {
    display: grid;

    grid-template-columns:
        42px
        1fr
        84px
        72px
        34px;

    gap: 6px;

    align-items: center;

    margin-top: 5px;
    margin-bottom: 3px;

    color: #6f7782;

    font-size: 8px;
    font-weight: 900;

    text-transform: uppercase;

    text-align: center;
}

.set-head div:first-child {
    text-align: left;
}

.set-row-label {
    display: flex;
    align-items: center;

    min-height: 42px;

    color: #8f97a2;

    font-size: 11px;
    font-weight: 900;
}

.set-prescribed {
    display: flex;
    align-items: center;
    justify-content: center;

    min-height: 42px;

    color: white;

    font-size: 11px;
    font-weight: 850;
}

.extra-badge {
    color: #ff5158;
}


/* =========================================================
   COMPACT NUMBER INPUTS
========================================================= */

[data-testid="stNumberInput"] {
    margin: 0 !important;
}

[data-testid="stNumberInput"] label {
    display: none !important;
}

[data-testid="stNumberInput"] > div {
    min-height: 42px !important;
}

[data-testid="stNumberInput"] input {
    min-height: 42px !important;
    height: 42px !important;

    padding-left: 4px !important;
    padding-right: 4px !important;

    text-align: center !important;

    font-size: 14px !important;
    font-weight: 900 !important;
}

[data-testid="stNumberInput"] button {
    min-width: 26px !important;
    width: 26px !important;

    padding: 0 !important;
}


/* =========================================================
   CHECKBOX
========================================================= */

[data-testid="stCheckbox"] {
    display: flex;
    align-items: center;
    justify-content: center;

    min-height: 42px;

    margin: 0 !important;
}


/* =========================================================
   BUTTONS
========================================================= */

.stButton > button {
    width: 100%;
    min-height: 45px;

    border-radius: 13px;

    border: 1px solid #31363e;

    background: #181b20;

    color: white;

    font-weight: 800;

    transition: .15s;
}

.stButton > button:hover {
    color: white;
    border-color: #ff4148;
    background: #20242a;
}

.stButton > button[kind="primary"] {
    border: none;

    background:
        linear-gradient(
            135deg,
            #ff3038,
            #ef3139
        );

    color: white;
}


/* =========================================================
   REST
========================================================= */

.rest-card {
    margin-top: 16px;
    padding: 13px;

    border-radius: 15px;
    border: 1px solid #292e35;

    background: #15181d;

    display: flex;
    justify-content: space-between;
    align-items: center;
}

.rest-label {
    color: #858d98;
    font-size: 11px;
    font-weight: 900;
}

.rest-time {
    color: white;
    font-size: 20px;
    font-weight: 900;
}


/* =========================================================
   BOTTOM NAV
========================================================= */

.bottom-nav {
    position: fixed;

    left: 50%;
    bottom: 0;

    transform: translateX(-50%);

    width: min(620px, 100%);
    height: 70px;

    z-index: 999;

    display: flex;
    align-items: center;
    justify-content: space-around;

    border-top: 1px solid #292d33;

    background: rgba(10,12,15,.97);

    backdrop-filter: blur(15px);
}

.bottom-nav-item {
    flex: 1;
    text-align: center;

    color: #747c87;

    font-size: 9px;
    font-weight: 800;
}

.bottom-nav-icon {
    font-size: 19px;
    line-height: 21px;
}

.bottom-nav-label {
    margin-top: 2px;
}

.bottom-nav-active {
    color: #ff464d;
}


/* =========================================================
   MOBILE
========================================================= */

@media (max-width: 600px) {

    .block-container {
        padding-top: 12px;
        padding-left: 12px;
        padding-right: 12px;
        padding-bottom: 95px;
    }

    .hello {
        font-size: 26px;
    }

    .hero {
        border-radius: 21px;
        padding: 19px;
    }

    .hero-title {
        font-size: 28px;
    }

    .exercise-visual {
        min-height: 80px;
        padding: 9px;
    }

    .exercise-thumb {
        width: 58px;
        height: 58px;
        min-width: 58px;
    }

    .exercise-name {
        font-size: 15px;
    }

    .exercise-open-button button {
        margin-top: -88px !important;
        height: 80px !important;
    }

    .detail-name {
        font-size: 28px;
    }

    .media-placeholder {
        height: 115px;
    }

    .set-head {
        grid-template-columns:
            34px
            1fr
            78px
            68px
            30px;

        gap: 4px;
    }

}


/* =========================================================
   VERY SMALL PHONES
========================================================= */

@media (max-width: 390px) {

    .set-head {
        grid-template-columns:
            30px
            1fr
            72px
            62px
            28px;

        gap: 3px;
    }

    [data-testid="stNumberInput"] input {
        font-size: 12px !important;
    }

    [data-testid="stNumberInput"] button {
        min-width: 22px !important;
        width: 22px !important;
    }

}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# HELPERS
# ============================================================

def safe(value):
    if value is None:
        return ""
    return html.escape(str(value))


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


def get_set_key(
    we_id,
    set_number,
    field
):
    return (
        f"we_{we_id}_"
        f"set_{set_number}_"
        f"{field}"
    )


def prescription_text(sets):

    if not sets:
        return "Serie non impostate"

    signatures = []

    for s in sets:
        signatures.append(
            (
                s.get("target_reps"),
                s.get("target_weight_kg"),
            )
        )

    if (
        len(signatures) > 0
        and len(set(signatures)) == 1
    ):

        reps = sets[0].get(
            "target_reps"
        )

        weight = sets[0].get(
            "target_weight_kg"
        )

        if (
            reps is not None
            and weight is not None
        ):
            return (
                f"{len(sets)} × {reps} "
                f"@ {format_weight(weight)} kg"
            )

        if reps is not None:
            return (
                f"{len(sets)} × {reps}"
            )

    pieces = []

    for s in sets:

        reps = s.get(
            "target_reps"
        )

        weight = s.get(
            "target_weight_kg"
        )

        if (
            reps is not None
            and weight is not None
        ):
            pieces.append(
                f"{reps}×"
                f"{format_weight(weight)}kg"
            )

        elif reps is not None:
            pieces.append(
                f"{reps} reps"
            )

    return " • ".join(pieces)


def prescribed_set_text(
    prescribed_set
):

    reps = prescribed_set.get(
        "target_reps"
    )

    weight = prescribed_set.get(
        "target_weight_kg"
    )

    if (
        reps is not None
        and weight is not None
    ):
        return (
            f"{reps} × "
            f"{format_weight(weight)}"
        )

    if reps is not None:
        return f"{reps} reps"

    if weight is not None:
        return (
            f"{format_weight(weight)} kg"
        )

    return "—"


def completed_sets(item):

    we_id = (
        item["workout_exercise"]["id"]
    )

    completed = 0

    for s in item["sets"]:

        done_key = get_set_key(
            we_id,
            s["set_number"],
            "done",
        )

        if st.session_state.get(
            done_key,
            False,
        ):
            completed += 1

    extra_count = st.session_state.get(
        f"extra_count_{we_id}",
        0,
    )

    for i in range(extra_count):

        done_key = get_set_key(
            we_id,
            f"extra_{i}",
            "done",
        )

        if st.session_state.get(
            done_key,
            False,
        ):
            completed += 1

    return completed


def total_sets(item):

    we_id = (
        item["workout_exercise"]["id"]
    )

    extras = st.session_state.get(
        f"extra_count_{we_id}",
        0,
    )

    return (
        len(item["sets"])
        + extras
    )


def exercise_status(item):

    done = completed_sets(item)
    total = total_sets(item)

    if (
        total > 0
        and done >= total
    ):
        return "done"

    if done > 0:
        return "active"

    return "todo"


def total_progress():

    total = 0
    done = 0

    for item in DATA["exercises"]:

        total += total_sets(item)
        done += completed_sets(item)

    if total == 0:
        return 0

    return round(
        (done / total) * 100
    )


def find_exercise(we_id):

    for item in DATA["exercises"]:

        current_id = (
            item["workout_exercise"]["id"]
        )

        if current_id == we_id:
            return item

    return None


def open_exercise(we_id):

    st.session_state.selected_exercise = (
        we_id
    )

    st.session_state.training_started = (
        True
    )

    st.session_state.screen = (
        "exercise"
    )

    st.rerun()


# ============================================================
# NAV
# ============================================================

def bottom_nav(active="today"):

    today_class = (
        "bottom-nav-active"
        if active == "today"
        else ""
    )

    program_class = (
        "bottom-nav-active"
        if active == "program"
        else ""
    )

    progress_class = (
        "bottom-nav-active"
        if active == "progress"
        else ""
    )

    profile_class = (
        "bottom-nav-active"
        if active == "profile"
        else ""
    )

    nav_html = (
        '<div class="bottom-nav">'
        f'<div class="bottom-nav-item {today_class}">'
        '<div class="bottom-nav-icon">⌂</div>'
        '<div class="bottom-nav-label">Oggi</div>'
        '</div>'
        f'<div class="bottom-nav-item {program_class}">'
        '<div class="bottom-nav-icon">▤</div>'
        '<div class="bottom-nav-label">Programma</div>'
        '</div>'
        f'<div class="bottom-nav-item {progress_class}">'
        '<div class="bottom-nav-icon">▥</div>'
        '<div class="bottom-nav-label">Progressi</div>'
        '</div>'
        f'<div class="bottom-nav-item {profile_class}">'
        '<div class="bottom-nav-icon">○</div>'
        '<div class="bottom-nav-label">Profilo</div>'
        '</div>'
        '</div>'
    )

    st.markdown(
        nav_html,
        unsafe_allow_html=True,
    )


# ============================================================
# HOME
# ============================================================

def render_home():

    athlete = DATA["athlete"]
    workout = DATA["workout"]
    program = DATA["program"]

    first_name = safe(
        athlete.get(
            "first_name",
            "Atleta",
        )
    )

    first_letter = (
        first_name[0].upper()
        if first_name
        else "A"
    )

    program_name = safe(
        program.get(
            "name",
            "Programma",
        )
    )

    workout_name = safe(
        workout.get(
            "name",
            "Allenamento",
        )
    )

    header_html = (
        '<div class="app-top">'
        '<div class="logo">'
        'TRAINING '
        '<span class="logo-red">HUB</span>'
        '</div>'
        f'<div class="avatar">{first_letter}</div>'
        '</div>'
    )

    st.markdown(
        header_html,
        unsafe_allow_html=True,
    )

    intro_html = (
        f'<div class="hello">'
        f'Ciao, {first_name} 👋'
        '</div>'
        f'<div class="program-name">'
        f'{program_name}'
        '</div>'
    )

    st.markdown(
        intro_html,
        unsafe_allow_html=True,
    )

    progress = total_progress()

    exercise_count = len(
        DATA["exercises"]
    )

    block_count = len(
        DATA["blocks"]
    )

    minutes = (
        workout.get(
            "estimated_minutes"
        )
        or "—"
    )

    hero_html = (
        '<div class="hero">'
        '<div class="hero-label">'
        'ALLENAMENTO DI OGGI'
        '</div>'
        f'<div class="hero-title">'
        f'{workout_name}'
        '</div>'
        '<div class="hero-sub">'
        'La tua sessione è pronta.'
        '</div>'
        '<div class="stats">'
        '<div class="stat">'
        f'<div class="stat-number">'
        f'{exercise_count}'
        '</div>'
        '<div class="stat-label">'
        'Esercizi'
        '</div>'
        '</div>'
        '<div class="stat">'
        f'<div class="stat-number">'
        f'{minutes}′'
        '</div>'
        '<div class="stat-label">'
        'Durata'
        '</div>'
        '</div>'
        '<div class="stat">'
        f'<div class="stat-number">'
        f'{block_count}'
        '</div>'
        '<div class="stat-label">'
        'Blocchi'
        '</div>'
        '</div>'
        '</div>'
        '<div class="progress-bg">'
        f'<div class="progress-fill" '
        f'style="width:{progress}%;">'
        '</div>'
        '</div>'
        '</div>'
    )

    st.markdown(
        hero_html,
        unsafe_allow_html=True,
    )

    if st.session_state.training_started:
        start_label = (
            "▶ CONTINUA ALLENAMENTO"
        )
    else:
        start_label = (
            "▶ INIZIA ALLENAMENTO"
        )

    if st.button(
        start_label,
        type="primary",
        use_container_width=True,
        key="home_start",
    ):

        st.session_state.training_started = (
            True
        )

        go("workout")

    st.markdown(
        '<div class="section-title">'
        'IL TUO PROGRAMMA'
        '</div>',
        unsafe_allow_html=True,
    )

    program_card = (
        '<div class="exercise-visual">'
        '<div class="exercise-info">'
        f'<div class="exercise-name">'
        f'{program_name}'
        '</div>'
        '<div class="exercise-prescription">'
        'Scheda, esercizi e progressi'
        '</div>'
        '</div>'
        '<div class="exercise-chevron">›</div>'
        '</div>'
    )

    st.markdown(
        program_card,
        unsafe_allow_html=True,
    )

    bottom_nav("today")


# ============================================================
# CLICKABLE EXERCISE CARD
# ============================================================

def render_exercise_card(item):

    exercise = item["exercise"]
    we = item["workout_exercise"]

    exercise_name = safe(
        exercise.get(
            "name",
            "Esercizio",
        )
    )

    code = safe(
        we.get(
            "exercise_code"
        )
        or ""
    )

    done = completed_sets(
        item
    )

    total = total_sets(
        item
    )

    status = exercise_status(
        item
    )

    if status == "done":

        status_html = (
            '<span class="status-done">'
            '✓ COMPLETATO'
            '</span>'
        )

    elif status == "active":

        status_html = (
            '<span class="status-active">'
            '● IN CORSO'
            '</span>'
        )

    else:

        status_html = (
            '<span class="status-todo">'
            '○ DA FARE'
            '</span>'
        )

    image_url = exercise.get(
        "image_url"
    )

    if image_url:

        image_html = (
            '<div class="exercise-thumb">'
            f'<img src="{safe(image_url)}" '
            'alt="Esercizio">'
            '</div>'
        )

    else:

        image_html = (
            '<div class="exercise-thumb">'
            '🏋️'
            '</div>'
        )

    prescription = safe(
        prescription_text(
            item["sets"]
        )
    )

    rest = (
        we.get(
            "default_rest_seconds"
        )
        or "—"
    )

    card_html = (
        '<div class="exercise-click-wrap">'
        '<div class="exercise-visual">'
        f'{image_html}'
        '<div class="exercise-info">'
        f'<div class="exercise-code">'
        f'{code}'
        '</div>'
        f'<div class="exercise-name">'
        f'{exercise_name}'
        '</div>'
        '<div class="exercise-prescription">'
        f'{prescription}'
        '</div>'
        '<div class="exercise-progress">'
        f'{done}/{total} serie'
        '&nbsp;•&nbsp;'
        f'⏱ {rest}s'
        '&nbsp;•&nbsp;'
        f'{status_html}'
        '</div>'
        '</div>'
        '<div class="exercise-chevron">'
        '›'
        '</div>'
        '</div>'
        '</div>'
    )

    st.markdown(
        card_html,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="exercise-open-button">',
        unsafe_allow_html=True,
    )

    clicked = st.button(
        exercise_name,
        key=f"open_{we['id']}",
        use_container_width=True,
    )

    st.markdown(
        '</div>',
        unsafe_allow_html=True,
    )

    if clicked:
        open_exercise(
            we["id"]
        )


# ============================================================
# WORKOUT OVERVIEW
# ============================================================

def render_workout():

    workout = DATA["workout"]

    workout_name = safe(
        workout.get(
            "name",
            "Allenamento",
        )
    )

    col_back, col_title = st.columns(
        [0.18, 0.82]
    )

    with col_back:

        if st.button(
            "‹",
            key="back_home",
        ):
            go("home")

    with col_title:

        title_html = (
            '<div style="'
            'font-size:22px;'
            'font-weight:900;'
            'padding-top:7px;'
            'color:white;'
            '">'
            f'{workout_name}'
            '</div>'
        )

        st.markdown(
            title_html,
            unsafe_allow_html=True,
        )

    progress = total_progress()

    workout_meta = (
        '<div style="'
        'display:flex;'
        'justify-content:space-between;'
        'color:#858c96;'
        'font-size:12px;'
        'margin-top:8px;'
        '">'
        f'<span>{len(DATA["exercises"])} esercizi</span>'
        f'<span>{progress}% completato</span>'
        '</div>'
        '<div class="progress-bg">'
        f'<div class="progress-fill" '
        f'style="width:{progress}%;">'
        '</div>'
        '</div>'
    )

    st.markdown(
        workout_meta,
        unsafe_allow_html=True,
    )

    grouped = {}

    for item in DATA["exercises"]:

        block_id = (
            item["workout_exercise"]
            .get("block_id")
        )

        grouped.setdefault(
            block_id,
            []
        ).append(item)

    for block in DATA["blocks"]:

        items = grouped.get(
            block["id"],
            [],
        )

        if not items:
            continue

        block_name = safe(
            block.get(
                "name",
                "Blocco",
            )
        )

        st.markdown(
            (
                '<div class="section-title">'
                f'{block_name}'
                '</div>'
            ),
            unsafe_allow_html=True,
        )

        for item in items:
            render_exercise_card(
                item
            )

    ungrouped = grouped.get(
        None,
        [],
    )

    if ungrouped:

        st.markdown(
            '<div class="section-title">'
            'ALTRI ESERCIZI'
            '</div>',
            unsafe_allow_html=True,
        )

        for item in ungrouped:
            render_exercise_card(
                item
            )

    bottom_nav("today")


# ============================================================
# EXERCISE DETAIL
# ============================================================

def render_exercise():

    we_id = (
        st.session_state
        .selected_exercise
    )

    item = find_exercise(
        we_id
    )

    if not item:

        st.session_state.screen = (
            "workout"
        )

        st.rerun()

    exercise = item["exercise"]
    we = item["workout_exercise"]
    sets = item["sets"]

    # --------------------------------------------------------
    # BACK
    # --------------------------------------------------------

    if st.button(
        "‹  TUTTI GLI ESERCIZI",
        key="back_workout",
    ):
        go("workout")

    exercise_name = safe(
        exercise.get(
            "name",
            "Esercizio",
        )
    )

    code = safe(
        we.get(
            "exercise_code"
        )
        or ""
    )

    category = safe(
        exercise.get(
            "category"
        )
        or ""
    )

    detail_header = (
        f'<div class="detail-code">'
        f'{code}'
        '</div>'
        f'<div class="detail-name">'
        f'{exercise_name}'
        '</div>'
        f'<div class="detail-category">'
        f'{category}'
        '</div>'
    )

    st.markdown(
        detail_header,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # IMAGE
    # --------------------------------------------------------

    image_url = exercise.get(
        "image_url"
    )

    if image_url:

        st.image(
            image_url,
            use_container_width=True,
        )

    else:

        st.markdown(
            '<div class="media-placeholder">'
            '🏋️'
            '</div>',
            unsafe_allow_html=True,
        )

    # --------------------------------------------------------
    # VIDEO
    # --------------------------------------------------------

    video_url = exercise.get(
        "video_url"
    )

    if video_url:

        st.link_button(
            "▶ GUARDA VIDEO",
            video_url,
            use_container_width=True,
        )

    # --------------------------------------------------------
    # DESCRIPTION
    # --------------------------------------------------------

    description = exercise.get(
        "description"
    )

    if description:

        st.caption(
            description
        )

    # --------------------------------------------------------
    # COACH NOTE
    # --------------------------------------------------------

    coach_notes = we.get(
        "coach_notes"
    )

    if coach_notes:

        note_html = (
            '<div class="coach-note">'
            '<div class="coach-note-title">'
            'NOTA COACH'
            '</div>'
            f'{safe(coach_notes)}'
            '</div>'
        )

        st.markdown(
            note_html,
            unsafe_allow_html=True,
        )

    # --------------------------------------------------------
    # SERIES
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">'
        'SERIE'
        '</div>',
        unsafe_allow_html=True,
    )

    # desktop/table heading
    head_cols = st.columns(
        [0.48, 1.2, 1.0, 0.85, 0.35],
        gap="small",
    )

    headings = [
        "SET",
        "PRESCRITTO",
        "KG",
        "REPS",
        "✓",
    ]

    for col, label in zip(
        head_cols,
        headings,
    ):

        with col:
            st.markdown(
                (
                    '<div style="'
                    'color:#737b86;'
                    'font-size:9px;'
                    'font-weight:900;'
                    'text-align:center;'
                    'margin-bottom:2px;'
                    '">'
                    f'{label}'
                    '</div>'
                ),
                unsafe_allow_html=True,
            )

    # --------------------------------------------------------
    # PRESCRIBED SETS
    # --------------------------------------------------------

    for prescribed_set in sets:

        set_number = (
            prescribed_set[
                "set_number"
            ]
        )

        target_reps = (
            prescribed_set.get(
                "target_reps"
            )
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

        reps_default = (
            int(target_reps)
            if target_reps is not None
            else 0
        )

        kg_key = get_set_key(
            we_id,
            set_number,
            "kg",
        )

        reps_key = get_set_key(
            we_id,
            set_number,
            "reps",
        )

        done_key = get_set_key(
            we_id,
            set_number,
            "done",
        )

        if kg_key not in st.session_state:
            st.session_state[
                kg_key
            ] = weight_default

        if reps_key not in st.session_state:
            st.session_state[
                reps_key
            ] = reps_default

        prescribed_text = safe(
            prescribed_set_text(
                prescribed_set
            )
        )

        row = st.columns(
            [0.48, 1.2, 1.0, 0.85, 0.35],
            gap="small",
        )

        with row[0]:

            st.markdown(
                (
                    '<div style="'
                    'height:42px;'
                    'display:flex;'
                    'align-items:center;'
                    'justify-content:center;'
                    'font-size:13px;'
                    'font-weight:900;'
                    'color:#8f97a2;'
                    '">'
                    f'{set_number}'
                    '</div>'
                ),
                unsafe_allow_html=True,
            )

        with row[1]:

            st.markdown(
                (
                    '<div style="'
                    'height:42px;'
                    'display:flex;'
                    'align-items:center;'
                    'justify-content:center;'
                    'font-size:12px;'
                    'font-weight:850;'
                    'color:white;'
                    '">'
                    f'{prescribed_text}'
                    '</div>'
                ),
                unsafe_allow_html=True,
            )

        with row[2]:

            st.number_input(
                "KG",
                min_value=0.0,
                step=2.5,
                key=kg_key,
                label_visibility="collapsed",
            )

        with row[3]:

            st.number_input(
                "REPS",
                min_value=0,
                step=1,
                key=reps_key,
                label_visibility="collapsed",
            )

        with row[4]:

            st.checkbox(
                "✓",
                key=done_key,
                label_visibility="collapsed",
            )

    # --------------------------------------------------------
    # EXTRA SETS
    # --------------------------------------------------------

    extra_key = (
        f"extra_count_{we_id}"
    )

    if extra_key not in st.session_state:
        st.session_state[
            extra_key
        ] = 0

    extra_count = (
        st.session_state[
            extra_key
        ]
    )

    for i in range(
        extra_count
    ):

        extra_number = i + 1

        kg_key = get_set_key(
            we_id,
            f"extra_{i}",
            "kg",
        )

        reps_key = get_set_key(
            we_id,
            f"extra_{i}",
            "reps",
        )

        done_key = get_set_key(
            we_id,
            f"extra_{i}",
            "done",
        )

        row = st.columns(
            [0.48, 1.2, 1.0, 0.85, 0.35],
            gap="small",
        )

        with row[0]:

            st.markdown(
                (
                    '<div style="'
                    'height:42px;'
                    'display:flex;'
                    'align-items:center;'
                    'justify-content:center;'
                    'font-size:12px;'
                    'font-weight:900;'
                    'color:#ff5158;'
                    '">'
                    f'+{extra_number}'
                    '</div>'
                ),
                unsafe_allow_html=True,
            )

        with row[1]:

            st.markdown(
                (
                    '<div style="'
                    'height:42px;'
                    'display:flex;'
                    'align-items:center;'
                    'justify-content:center;'
                    'font-size:10px;'
                    'font-weight:900;'
                    'color:#ff5158;'
                    '">'
                    'EXTRA'
                    '</div>'
                ),
                unsafe_allow_html=True,
            )

        with row[2]:

            st.number_input(
                "KG",
                min_value=0.0,
                step=2.5,
                key=kg_key,
                label_visibility="collapsed",
            )

        with row[3]:

            st.number_input(
                "REPS",
                min_value=0,
                step=1,
                key=reps_key,
                label_visibility="collapsed",
            )

        with row[4]:

            st.checkbox(
                "✓",
                key=done_key,
                label_visibility="collapsed",
            )

    if st.button(
        "＋ AGGIUNGI SERIE",
        key=f"add_set_{we_id}",
    ):

        st.session_state[
            extra_key
        ] += 1

        st.rerun()

    # --------------------------------------------------------
    # REST
    # --------------------------------------------------------

    rest = (
        we.get(
            "default_rest_seconds"
        )
        or 0
    )

    if rest:

        minutes = rest // 60
        seconds = rest % 60

        rest_html = (
            '<div class="rest-card">'
            '<div class="rest-label">'
            '⏱ RECUPERO'
            '</div>'
            '<div class="rest-time">'
            f'{minutes:02d}:{seconds:02d}'
            '</div>'
            '</div>'
        )

        st.markdown(
            rest_html,
            unsafe_allow_html=True,
        )

    # --------------------------------------------------------
    # NEXT EXERCISE
    # --------------------------------------------------------

    current_index = None

    for index, candidate in enumerate(
        DATA["exercises"]
    ):

        candidate_id = (
            candidate[
                "workout_exercise"
            ]["id"]
        )

        if candidate_id == we_id:
            current_index = index
            break

    if (
        current_index is not None
        and current_index
        < len(DATA["exercises"]) - 1
    ):

        next_item = (
            DATA["exercises"][
                current_index + 1
            ]
        )

        next_name = safe(
            next_item[
                "exercise"
            ]["name"]
        )

        next_id = (
            next_item[
                "workout_exercise"
            ]["id"]
        )

        st.markdown(
            '<div style="height:10px;"></div>',
            unsafe_allow_html=True,
        )

        if st.button(
            f"PROSSIMO: "
            f"{next_name.upper()}  →",
            key=f"next_{we_id}",
        ):

            open_exercise(
                next_id
            )

    bottom_nav("today")


# ============================================================
# ROUTER
# ============================================================

if (
    st.session_state.screen
    == "home"
):

    render_home()

elif (
    st.session_state.screen
    == "workout"
):

    render_workout()

elif (
    st.session_state.screen
    == "exercise"
):

    render_exercise()

else:

    st.session_state.screen = (
        "home"
    )

    st.rerun()
