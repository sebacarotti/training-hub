import streamlit as st
import requests
import html

# ============================================================
# TRAINING HUB V4
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

/* ----------------------------------------------------------
   STREAMLIT
---------------------------------------------------------- */

#MainMenu,
footer,
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


/* ----------------------------------------------------------
   HEADER
---------------------------------------------------------- */

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


/* ----------------------------------------------------------
   HOME
---------------------------------------------------------- */

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


/* ----------------------------------------------------------
   HERO
---------------------------------------------------------- */

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
        0 20px 45px rgba(0,0,0,.28);

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


/* ----------------------------------------------------------
   PROGRESS
---------------------------------------------------------- */

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


/* ----------------------------------------------------------
   SECTION
---------------------------------------------------------- */

.section-title {
    color: #858c97;

    font-size: 11px;
    font-weight: 900;

    letter-spacing: 1.4px;

    text-transform: uppercase;

    margin-top: 27px;
    margin-bottom: 10px;
}


/* ----------------------------------------------------------
   REAL CLICKABLE EXERCISE BUTTON
---------------------------------------------------------- */

/*
Il pulsante contiene tutto.
Non esiste più una card HTML separata.
*/

div[data-testid="stButton"] button[kind="secondary"] {
    white-space: pre-wrap;
}


/*
I pulsanti esercizio hanno una key che comincia
con exercise_card_.
Streamlit espone la key nel DOM tramite
st-key-...
*/

div[class*="st-key-exercise_card_"] button {

    width: 100%;

    min-height: 102px;

    padding:
        13px
        48px
        13px
        88px;

    position: relative;

    border-radius: 18px;

    border:
        1px solid
        #2c3138;

    background:
        #14171c;

    color: white;

    text-align: left;

    justify-content: flex-start;

    box-shadow: none;

    transition:
        border-color .15s,
        background .15s,
        transform .08s;

    overflow: hidden;
}


div[class*="st-key-exercise_card_"] button:hover {

    background:
        #191d22;

    border-color:
        #414751;

    color: white;
}


div[class*="st-key-exercise_card_"] button:active {

    transform:
        scale(.99);

    border-color:
        #ff454c;
}


/* ----------------------------------------------------------
   IMMAGINE CARD
---------------------------------------------------------- */

/*
Pseudo-elemento = area immagine.
Per ora mostriamo 🏋️.
Quando metteremo immagini vere cambieremo questo.
*/

div[class*="st-key-exercise_card_"] button::before {

    content: "🏋️";

    position: absolute;

    left: 13px;
    top: 50%;

    transform:
        translateY(-50%);

    width: 62px;
    height: 62px;

    display: flex;

    align-items: center;
    justify-content: center;

    border-radius: 13px;

    background:
        linear-gradient(
            145deg,
            #292e35,
            #1b1f25
        );

    font-size: 25px;
}


/* ----------------------------------------------------------
   FRECCIA
---------------------------------------------------------- */

div[class*="st-key-exercise_card_"] button::after {

    content: "›";

    position: absolute;

    right: 17px;
    top: 50%;

    transform:
        translateY(-50%);

    color: #7e8793;

    font-size: 29px;

    font-weight: 300;
}


/* ----------------------------------------------------------
   TESTO CARD
---------------------------------------------------------- */

div[class*="st-key-exercise_card_"] button p {

    margin: 0;

    width: 100%;

    color: white;

    font-size: 14px;

    line-height: 1.45;

    text-align: left;
}


/* ----------------------------------------------------------
   DETAIL
---------------------------------------------------------- */

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


/* ----------------------------------------------------------
   MEDIA
---------------------------------------------------------- */

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


/* ----------------------------------------------------------
   COACH
---------------------------------------------------------- */

.coach-note {

    margin-top: 13px;

    padding: 12px;

    border-radius: 12px;

    border-left:
        3px solid #ff4148;

    background:
        #171b20;

    color:
        #abb1ba;

    font-size:
        12px;

    line-height:
        1.45;
}

.coach-note-title {

    color:
        white;

    font-weight:
        900;

    font-size:
        10px;

    letter-spacing:
        1px;
}


/* ----------------------------------------------------------
   NUMBER INPUT
---------------------------------------------------------- */

[data-testid="stNumberInput"] {

    margin:
        0 !important;
}

[data-testid="stNumberInput"] label {

    display:
        none !important;
}

[data-testid="stNumberInput"] input {

    min-height:
        42px !important;

    height:
        42px !important;

    padding-left:
        3px !important;

    padding-right:
        3px !important;

    text-align:
        center !important;

    font-size:
        13px !important;

    font-weight:
        900 !important;
}

[data-testid="stNumberInput"] button {

    min-width:
        24px !important;

    width:
        24px !important;

    padding:
        0 !important;
}


/* ----------------------------------------------------------
   CHECKBOX
---------------------------------------------------------- */

[data-testid="stCheckbox"] {

    display:
        flex;

    align-items:
        center;

    justify-content:
        center;

    min-height:
        42px;

    margin:
        0 !important;
}


/* ----------------------------------------------------------
   GENERIC BUTTON
---------------------------------------------------------- */

.stButton > button {

    width:
        100%;

    min-height:
        45px;

    border-radius:
        13px;

    border:
        1px solid #31363e;

    background:
        #181b20;

    color:
        white;

    font-weight:
        800;
}

.stButton > button:hover {

    color:
        white;

    border-color:
        #ff4148;

    background:
        #20242a;
}

.stButton > button[kind="primary"] {

    border:
        none;

    background:
        linear-gradient(
            135deg,
            #ff3038,
            #ef3139
        );

    color:
        white;
}


/* ----------------------------------------------------------
   REST
---------------------------------------------------------- */

.rest-card {

    margin-top:
        16px;

    padding:
        13px;

    border-radius:
        15px;

    border:
        1px solid #292e35;

    background:
        #15181d;

    display:
        flex;

    justify-content:
        space-between;

    align-items:
        center;
}

.rest-label {

    color:
        #858d98;

    font-size:
        11px;

    font-weight:
        900;
}

.rest-time {

    color:
        white;

    font-size:
        20px;

    font-weight:
        900;
}


/* ----------------------------------------------------------
   BOTTOM NAV
---------------------------------------------------------- */

.bottom-nav {

    position:
        fixed;

    left:
        50%;

    bottom:
        0;

    transform:
        translateX(-50%);

    width:
        min(620px, 100%);

    height:
        70px;

    z-index:
        999;

    display:
        flex;

    align-items:
        center;

    justify-content:
        space-around;

    border-top:
        1px solid #292d33;

    background:
        rgba(10,12,15,.97);

    backdrop-filter:
        blur(15px);
}

.bottom-nav-item {

    flex:
        1;

    text-align:
        center;

    color:
        #747c87;

    font-size:
        9px;

    font-weight:
        800;
}

.bottom-nav-icon {

    font-size:
        19px;

    line-height:
        21px;
}

.bottom-nav-label {

    margin-top:
        2px;
}

.bottom-nav-active {

    color:
        #ff464d;
}


/* ----------------------------------------------------------
   MOBILE
---------------------------------------------------------- */

@media (max-width: 600px) {

    .block-container {

        padding-top:
            12px;

        padding-left:
            12px;

        padding-right:
            12px;

        padding-bottom:
            95px;
    }

    .hello {

        font-size:
            26px;
    }

    .hero {

        border-radius:
            21px;

        padding:
            19px;
    }

    .hero-title {

        font-size:
            28px;
    }

    div[class*="st-key-exercise_card_"] button {

        min-height:
            92px;

        padding-left:
            80px;

        padding-right:
            38px;

        padding-top:
            10px;

        padding-bottom:
            10px;
    }

    div[class*="st-key-exercise_card_"] button::before {

        width:
            55px;

        height:
            55px;

        left:
            11px;

        font-size:
            22px;
    }

    div[class*="st-key-exercise_card_"] button::after {

        right:
            13px;

        font-size:
            26px;
    }

    div[class*="st-key-exercise_card_"] button p {

        font-size:
            12px;

        line-height:
            1.42;
    }

    .detail-name {

        font-size:
            28px;
    }

    .media-placeholder {

        height:
            115px;
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

    return html.escape(
        str(value)
    )


def go(screen):

    st.session_state.screen = (
        screen
    )

    st.rerun()


def format_weight(value):

    if value is None:
        return ""

    value = float(value)

    if value.is_integer():
        return str(
            int(value)
        )

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
        signatures
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

    return " • ".join(
        pieces
    )


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

        return (
            f"{reps} reps"
        )

    if weight is not None:

        return (
            f"{format_weight(weight)} kg"
        )

    return "—"


def completed_sets(item):

    we_id = (
        item[
            "workout_exercise"
        ]["id"]
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

    extra_count = (
        st.session_state.get(
            f"extra_count_{we_id}",
            0,
        )
    )

    for i in range(
        extra_count
    ):

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
        item[
            "workout_exercise"
        ]["id"]
    )

    extras = (
        st.session_state.get(
            f"extra_count_{we_id}",
            0,
        )
    )

    return (
        len(item["sets"])
        + extras
    )


def exercise_status(item):

    done = completed_sets(
        item
    )

    total = total_sets(
        item
    )

    if (
        total > 0
        and done >= total
    ):

        return "COMPLETATO"

    if done > 0:

        return "IN CORSO"

    return "DA FARE"


def total_progress():

    total = 0
    done = 0

    for item in DATA["exercises"]:

        total += total_sets(
            item
        )

        done += completed_sets(
            item
        )

    if total == 0:

        return 0

    return round(
        (done / total) * 100
    )


def find_exercise(
    we_id
):

    for item in DATA["exercises"]:

        current_id = (
            item[
                "workout_exercise"
            ]["id"]
        )

        if current_id == we_id:

            return item

    return None


def open_exercise(
    we_id
):

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
# BOTTOM NAV
# ============================================================

def bottom_nav(
    active="today"
):

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
        '<span class="logo-red">'
        'HUB'
        '</span>'
        '</div>'
        f'<div class="avatar">'
        f'{first_letter}'
        '</div>'
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

    program_html = (
        '<div style="'
        'background:#14171c;'
        'border:1px solid #292e35;'
        'border-radius:17px;'
        'padding:15px;'
        '">'
        f'<div style="'
        'font-size:16px;'
        'font-weight:900;'
        'color:white;'
        '">'
        f'{program_name}'
        '</div>'
        '<div style="'
        'font-size:12px;'
        'color:#9299a4;'
        'margin-top:4px;'
        '">'
        'Scheda, esercizi e progressi'
        '</div>'
        '</div>'
    )

    st.markdown(
        program_html,
        unsafe_allow_html=True,
    )

    bottom_nav("today")


# ============================================================
# EXERCISE CARD
# ============================================================

def render_exercise_card(
    item
):

    exercise = item[
        "exercise"
    ]

    we = item[
        "workout_exercise"
    ]

    name = (
        exercise.get(
            "name",
            "Esercizio",
        )
    )

    code = (
        we.get(
            "exercise_code"
        )
        or ""
    )

    prescription = (
        prescription_text(
            item["sets"]
        )
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

    rest = (
        we.get(
            "default_rest_seconds"
        )
        or "—"
    )

    # --------------------------------------------------------
    # TESTO INTERNO DELLA CARD
    #
    # Usiamo un solo vero bottone Streamlit.
    # Tutta la card è cliccabile.
    # --------------------------------------------------------

    card_label = (
        f"{code}   {name}\n"
        f"{prescription}\n"
        f"{done}/{total} serie  •  "
        f"⏱ {rest}s  •  {status}"
    )

    if st.button(
        card_label,
        key=f"exercise_card_{we['id']}",
        use_container_width=True,
    ):

        open_exercise(
            we["id"]
        )


# ============================================================
# WORKOUT
# ============================================================

def render_workout():

    workout = DATA["workout"]

    workout_name = safe(
        workout.get(
            "name",
            "Allenamento",
        )
    )

    col_back, col_title = (
        st.columns(
            [0.18, 0.82]
        )
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

        f'<span>'
        f'{len(DATA["exercises"])} esercizi'
        '</span>'

        f'<span>'
        f'{progress}% completato'
        '</span>'

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
            item[
                "workout_exercise"
            ].get(
                "block_id"
            )
        )

        grouped.setdefault(
            block_id,
            [],
        ).append(
            item
        )

    # --------------------------------------------------------
    # BLOCKS
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # UNGROUPED
    # --------------------------------------------------------

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

    exercise = item[
        "exercise"
    ]

    we = item[
        "workout_exercise"
    ]

    sets = item[
        "sets"
    ]

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
    # COACH NOTES
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

    # HEADER

    header_cols = st.columns(
        [
            0.45,
            1.10,
            1.00,
            0.85,
            0.35,
        ],
        gap="small",
    )

    headers = [
        "SET",
        "PRESCR.",
        "KG",
        "REPS",
        "✓",
    ]

    for col, title in zip(
        header_cols,
        headers,
    ):

        with col:

            st.markdown(
                (
                    '<div style="'
                    'text-align:center;'
                    'color:#747c87;'
                    'font-size:8px;'
                    'font-weight:900;'
                    'margin-bottom:3px;'
                    '">'
                    f'{title}'
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
            float(
                target_weight
            )
            if target_weight is not None
            else 0.0
        )

        reps_default = (
            int(
                target_reps
            )
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

        if (
            kg_key
            not in st.session_state
        ):

            st.session_state[
                kg_key
            ] = weight_default

        if (
            reps_key
            not in st.session_state
        ):

            st.session_state[
                reps_key
            ] = reps_default

        prescribed = safe(
            prescribed_set_text(
                prescribed_set
            )
        )

        row = st.columns(
            [
                0.45,
                1.10,
                1.00,
                0.85,
                0.35,
            ],
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
                    'font-size:11px;'
                    'font-weight:850;'
                    'color:white;'
                    'text-align:center;'
                    '">'
                    f'{prescribed}'
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

    if (
        extra_key
        not in st.session_state
    ):

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
            [
                0.45,
                1.10,
                1.00,
                0.85,
                0.35,
            ],
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
                    'color:#ff5158;'
                    'font-weight:900;'
                    '">'
                    f'+{i + 1}'
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
                    'color:#ff5158;'
                    'font-size:9px;'
                    'font-weight:900;'
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

        minutes = (
            rest // 60
        )

        seconds = (
            rest % 60
        )

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

        next_name = (
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
