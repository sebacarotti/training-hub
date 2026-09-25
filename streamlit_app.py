import streamlit as st
import requests
import html

# ============================================================
# TRAINING HUB V7
# MOBILE FIRST
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
            "workout_exercise_id":
                f"in.({','.join(workout_exercise_ids)})",
            "order": "set_number.asc",
        },
    )

    exercises_by_id = {
        x["id"]: x
        for x in exercises
    }

    sets_by_we = {}

    for set_item in prescribed_sets:
        we_id = set_item["workout_exercise_id"]

        sets_by_we.setdefault(
            we_id,
            [],
        ).append(set_item)

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
                    [],
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
# LOAD DATA
# ============================================================

try:
    DATA = load_training()

except Exception as error:
    st.error(f"Errore database: {error}")
    st.stop()

if not DATA:
    st.error("Nessun programma trovato.")
    st.stop()


# ============================================================
# SESSION
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

/* ================================================
   BASE
================================================ */

#MainMenu,
footer,
header {
    visibility: hidden;
}

[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"] {
    display: none !important;
}

html,
body {
    background: #080b0e;
    overflow-x: hidden !important;
}

.stApp {
    background:
        radial-gradient(
            circle at 50% -10%,
            #182029 0%,
            #0c1014 35%,
            #07090b 76%
        );

    color: #ffffff;

    overflow-x: hidden !important;
}

.block-container {
    max-width: 620px;

    padding-top: 16px;
    padding-left: 16px;
    padding-right: 16px;
    padding-bottom: 100px;

    overflow-x: hidden !important;
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


/* ================================================
   GENERAL BUTTON
================================================ */

.stButton > button {
    width: 100%;
    min-height: 44px;

    border-radius: 14px;

    border: 1px solid #303640;

    background: #171b20;

    color: white;

    font-weight: 800;
}

.stButton > button:hover {
    color: white;

    border-color: #ff3d46;

    background: #20252c;
}

.stButton > button[kind="primary"] {
    color: white;

    border: none;

    background:
        linear-gradient(
            135deg,
            #ff3039,
            #ff484f
        );
}


/* ================================================
   HOME
================================================ */

.app-top {
    display: flex;
    justify-content: space-between;
    align-items: center;

    margin-bottom: 28px;
}

.logo {
    font-size: 18px;
    font-weight: 950;
    letter-spacing: 1px;
}

.logo-red {
    color: #ff3d46;
}

.avatar {
    width: 42px;
    height: 42px;

    display: flex;
    align-items: center;
    justify-content: center;

    border-radius: 50%;

    background: #20242a;

    border: 1px solid #353b44;

    font-weight: 900;
}

.hello {
    font-size: 30px;
    font-weight: 950;

    line-height: 1.1;
}

.program-name {
    margin-top: 7px;
    margin-bottom: 25px;

    color: #9299a4;

    font-size: 14px;
}


/* ================================================
   HERO
================================================ */

.hero {
    padding: 22px;

    margin-bottom: 13px;

    border-radius: 24px;

    border: 1px solid #303640;

    background:
        linear-gradient(
            145deg,
            #20242b,
            #12151a
        );
}

.hero-label {
    color: #ff5259;

    font-size: 11px;
    font-weight: 900;

    letter-spacing: 1.4px;
}

.hero-title {
    margin-top: 5px;

    font-size: 31px;
    font-weight: 950;
}

.hero-sub {
    margin-top: 3px;

    color: #949ba5;

    font-size: 13px;
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
    font-size: 19px;
    font-weight: 950;
}

.stat-label {
    margin-top: 2px;

    color: #717985;

    font-size: 9px;
    font-weight: 800;

    text-transform: uppercase;
}


/* ================================================
   PROGRESS
================================================ */

.progress-bg {
    width: 100%;
    height: 7px;

    margin-top: 17px;

    overflow: hidden;

    border-radius: 100px;

    background: #292d33;
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


/* ================================================
   TITLES
================================================ */

.section-title {
    margin-top: 26px;
    margin-bottom: 10px;

    color: #858d98;

    font-size: 11px;
    font-weight: 900;

    letter-spacing: 1.6px;

    text-transform: uppercase;
}


/* ================================================
   WORKOUT EXERCISE CARDS
================================================ */

div[class*="st-key-exercise_card_"] button {
    width: 100%;

    min-height: 94px;

    position: relative;

    padding:
        12px
        45px
        12px
        82px;

    overflow: hidden;

    border-radius: 18px;

    border: 1px solid #2c3138;

    background: #14171c;

    color: white;

    text-align: left;

    justify-content: flex-start;
}

div[class*="st-key-exercise_card_"] button::before {
    content: "🏋️";

    position: absolute;

    left: 12px;
    top: 50%;

    transform: translateY(-50%);

    width: 58px;
    height: 58px;

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

    font-size: 23px;
}

div[class*="st-key-exercise_card_"] button::after {
    content: "›";

    position: absolute;

    right: 15px;
    top: 50%;

    transform: translateY(-50%);

    color: #7e8793;

    font-size: 28px;
}

div[class*="st-key-exercise_card_"] button p {
    margin: 0;

    white-space: pre-wrap;

    text-align: left;

    font-size: 12px;

    line-height: 1.45;
}


/* ================================================
   EXERCISE DETAIL
================================================ */

.exercise-code {
    height: 42px;

    padding: 0 13px;

    display: flex;
    align-items: center;
    justify-content: center;

    border-radius: 14px;

    border: 1px solid #ff3d46;

    background:
        linear-gradient(
            145deg,
            #481b21,
            #2c1519
        );

    color: white;

    font-size: 13px;
    font-weight: 950;
}

.exercise-name {
    margin-top: 12px;
    margin-bottom: 5px;

    color: white;

    font-size: 32px;
    font-weight: 950;

    line-height: 1.05;
}

.exercise-category {
    margin-bottom: 15px;

    color: #8c949f;

    font-size: 14px;
}


/* ================================================
   EXERCISE IMAGE
================================================ */

.exercise-media {
    width: 100%;
    height: 190px;

    position: relative;

    display: flex;
    align-items: center;
    justify-content: center;

    overflow: hidden;

    margin-bottom: 11px;

    border-radius: 21px;

    border: 1px solid #292f37;

    background:
        radial-gradient(
            circle at 50% 42%,
            #242a31,
            #111419 70%
        );
}

.exercise-media-placeholder {
    font-size: 48px;
}

.exercise-description {
    margin-bottom: 13px;

    color: #a5acb5;

    font-size: 12px;

    line-height: 1.45;
}


/* ================================================
   EXERCISE STATS
================================================ */

.exercise-stats {
    display: grid;

    grid-template-columns:
        repeat(3, minmax(0, 1fr));

    gap: 7px;

    margin-top: 13px;
    margin-bottom: 27px;
}

.exercise-stat {
    min-width: 0;
    min-height: 67px;

    padding: 9px 7px;

    display: flex;
    align-items: center;

    gap: 7px;

    border-radius: 16px;

    border: 1px solid #292f37;

    background:
        linear-gradient(
            145deg,
            #191d22,
            #111419
        );
}

.exercise-stat-icon {
    width: 32px;
    height: 32px;

    flex: 0 0 32px;

    display: flex;
    align-items: center;
    justify-content: center;

    border-radius: 10px;

    background: #35171c;

    color: #ff4149;

    font-size: 15px;
}

.exercise-stat-value {
    color: white;

    font-size: 12px;
    font-weight: 950;

    white-space: nowrap;
}

.exercise-stat-label {
    margin-top: 2px;

    color: #777f8a;

    font-size: 7px;
    font-weight: 800;

    text-transform: uppercase;
}


/* ================================================
   SET TITLE
================================================ */

.set-title-row {
    display: flex;

    align-items: center;
    justify-content: space-between;

    margin-top: 6px;
    margin-bottom: 7px;
}

.set-title {
    color: #858d98;

    font-size: 11px;
    font-weight: 900;

    letter-spacing: 1.6px;
}

.set-progress {
    color: #ff464e;

    font-size: 10px;
    font-weight: 950;
}


/* ================================================
   SET HEADER + ROW

   IMPORTANT:
   no fixed desktop width
================================================ */

div[class*="st-key-set_header_"],
div[class*="st-key-setrow_"] {
    width: 100% !important;
    max-width: 100% !important;

    overflow: hidden !important;
}

div[class*="st-key-set_header_"]
[data-testid="stHorizontalBlock"],

div[class*="st-key-setrow_"]
[data-testid="stHorizontalBlock"] {

    width: 100% !important;
    max-width: 100% !important;

    display: grid !important;

    grid-template-columns:
        32px
        52px
        minmax(0, 1fr)
        minmax(0, 1fr)
        27px !important;

    gap: 4px !important;

    align-items: center !important;
}


/* Streamlit columns become grid children */

div[class*="st-key-set_header_"]
[data-testid="column"],

div[class*="st-key-setrow_"]
[data-testid="column"] {

    width: 100% !important;
    min-width: 0 !important;
    max-width: 100% !important;

    flex: none !important;
}


/* ================================================
   HEADER
================================================ */

.set-header-cell {
    height: 27px;

    display: flex;
    align-items: center;
    justify-content: center;

    color: #737c88;

    font-size: 7px;
    font-weight: 950;

    white-space: nowrap;
}


/* ================================================
   ROW CARD
================================================ */

div[class*="st-key-setrow_"] {
    margin-bottom: 6px;

    padding: 5px;

    border-radius: 13px;

    border: 1px solid #222831;

    background:
        linear-gradient(
            145deg,
            #12161b,
            #0e1115
        );
}

.set-number-box {
    width: 100%;
    height: 38px;

    display: flex;
    align-items: center;
    justify-content: center;

    border-radius: 9px;

    background: #1b2026;

    color: white;

    font-size: 11px;
    font-weight: 950;
}

.set-prescription {
    width: 100%;
    height: 38px;

    display: flex;
    align-items: center;
    justify-content: center;

    color: #a2a9b2;

    font-size: 8px;

    white-space: nowrap;

    text-align: center;
}

.extra-set-number {
    background: #35171c;

    color: #ff5058;
}

.extra-label {
    color: #ff5058;

    font-weight: 900;
}


/* ================================================
   NUMBER INPUT
================================================ */

div[class*="st-key-setrow_"]
[data-testid="stNumberInput"] {

    width: 100% !important;
    min-width: 0 !important;

    margin: 0 !important;
}

div[class*="st-key-setrow_"]
[data-testid="stNumberInput"] label {

    display: none !important;
}

div[class*="st-key-setrow_"]
[data-testid="stNumberInput"] > div {

    width: 100% !important;
    min-width: 0 !important;
}

div[class*="st-key-setrow_"]
[data-testid="stNumberInput"] input {

    width: 100% !important;
    min-width: 0 !important;

    height: 38px !important;
    min-height: 38px !important;

    padding:
        0
        18px !important;

    border-radius: 9px !important;

    text-align: center !important;

    font-size: 10px !important;
    font-weight: 900 !important;
}

div[class*="st-key-setrow_"]
[data-testid="stNumberInput"] button {

    width: 18px !important;
    min-width: 18px !important;

    height: 38px !important;

    padding: 0 !important;
}


/* ================================================
   CHECKBOX
================================================ */

div[class*="st-key-setrow_"]
[data-testid="stCheckbox"] {

    min-height: 38px !important;

    display: flex !important;

    align-items: center !important;
    justify-content: center !important;

    margin: 0 !important;
}

div[class*="st-key-setrow_"]
[data-testid="stCheckbox"] label {

    padding: 0 !important;
}


/* ================================================
   ADD SET
================================================ */

div[class*="st-key-add_set_"] button {

    min-height: 48px;

    margin-top: 8px;

    border-radius: 15px;

    border: 1px solid #353b44;

    background:
        linear-gradient(
            145deg,
            #171b20,
            #111419
        );

    font-size: 11px;

    letter-spacing: .7px;
}


/* ================================================
   REST PANEL
================================================ */

.rest-panel {
    min-height: 82px;

    margin-top: 17px;

    padding: 13px;

    display: flex;

    align-items: center;
    justify-content: space-between;

    gap: 7px;

    border-radius: 18px;

    border: 1px solid #ff3c45;

    background:
        radial-gradient(
            circle at 50% 50%,
            #37181d,
            #181216 70%
        );
}

.rest-left {
    color: #ff4c54;

    font-size: 9px;
    font-weight: 900;
}

.rest-clock {
    color: white;

    font-size: 26px;
    font-weight: 950;
}

.rest-actions {
    display: flex;

    align-items: center;

    gap: 4px;
}

.rest-mini {
    min-width: 34px;
    height: 34px;

    padding: 0 4px;

    display: flex;
    align-items: center;
    justify-content: center;

    border-radius: 10px;

    border: 1px solid #343a43;

    background: #252a31;

    color: white;

    font-size: 8px;
    font-weight: 900;
}

.rest-play {
    width: 40px;
    height: 40px;

    flex: 0 0 40px;

    display: flex;
    align-items: center;
    justify-content: center;

    border-radius: 50%;

    background:
        linear-gradient(
            145deg,
            #ff313b,
            #ff5057
        );

    font-size: 15px;
}


/* ================================================
   COACH NOTE
================================================ */

.coach-note {
    margin-top: 14px;

    padding: 14px;

    border-radius: 15px;

    border-left: 3px solid #ff3d46;

    background:
        linear-gradient(
            145deg,
            #161a1f,
            #101317
        );
}

.coach-note-title {
    margin-bottom: 5px;

    color: #ff464e;

    font-size: 9px;
    font-weight: 900;

    letter-spacing: 1px;
}

.coach-note-text {
    color: #abb2bb;

    font-size: 11px;

    line-height: 1.45;
}


/* ================================================
   BOTTOM NAV
================================================ */

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

    background: rgba(8,10,12,.97);

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


/* ================================================
   MOBILE
================================================ */

@media (max-width: 600px) {

    .block-container {
        width: 100% !important;
        max-width: 100% !important;

        padding-top: 12px;
        padding-left: 12px;
        padding-right: 12px;
        padding-bottom: 94px;

        overflow-x: hidden !important;
    }

    .hello {
        font-size: 26px;
    }

    .hero {
        padding: 19px;

        border-radius: 21px;
    }

    .hero-title {
        font-size: 28px;
    }

    .exercise-name {
        font-size: 30px;
    }

    .exercise-media {
        height: 155px;
    }

    .exercise-stats {
        gap: 5px;
    }

    .exercise-stat {
        min-height: 62px;

        padding: 7px 5px;

        gap: 5px;
    }

    .exercise-stat-icon {
        width: 28px;
        height: 28px;

        flex-basis: 28px;

        font-size: 13px;
    }

    .exercise-stat-value {
        font-size: 10px;
    }

    .exercise-stat-label {
        font-size: 6px;
    }


    /* TABLE MOBILE */

    div[class*="st-key-set_header_"]
    [data-testid="stHorizontalBlock"],

    div[class*="st-key-setrow_"]
    [data-testid="stHorizontalBlock"] {

        display: grid !important;

        grid-template-columns:
            30px
            49px
            minmax(0, 1fr)
            minmax(0, 1fr)
            25px !important;

        gap: 3px !important;

        width: 100% !important;
        max-width: 100% !important;

        overflow: hidden !important;
    }

    div[class*="st-key-setrow_"] {
        width: 100% !important;

        padding: 4px !important;

        margin-bottom: 5px;

        overflow: hidden !important;
    }

    .set-number-box,
    .set-prescription {
        height: 36px;
    }

    .set-number-box {
        font-size: 10px;
    }

    .set-prescription {
        font-size: 7px;
    }

    div[class*="st-key-setrow_"]
    [data-testid="stNumberInput"] input {

        height: 36px !important;
        min-height: 36px !important;

        padding:
            0
            15px !important;

        font-size: 9px !important;
    }

    div[class*="st-key-setrow_"]
    [data-testid="stNumberInput"] button {

        width: 16px !important;
        min-width: 16px !important;

        height: 36px !important;
    }

    div[class*="st-key-setrow_"]
    [data-testid="stCheckbox"] {

        min-height: 36px !important;
    }

    .rest-panel {
        min-height: 74px;

        padding: 10px 7px;
    }

    .rest-left {
        font-size: 7px;
    }

    .rest-clock {
        font-size: 21px;
    }

    .rest-mini {
        min-width: 29px;

        height: 31px;

        font-size: 7px;
    }

    .rest-play {
        width: 36px;
        height: 36px;

        flex-basis: 36px;
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


def format_rest(seconds):

    if not seconds:
        return "00:00"

    minutes = int(seconds) // 60
    secs = int(seconds) % 60

    return f"{minutes:02d}:{secs:02d}"


def get_set_key(
    workout_exercise_id,
    set_number,
    field,
):

    return (
        f"we_{workout_exercise_id}_"
        f"set_{set_number}_"
        f"{field}"
    )


def prescription_text(sets):

    if not sets:
        return "Serie non impostate"

    signatures = [
        (
            item.get("target_reps"),
            item.get("target_weight_kg"),
        )
        for item in sets
    ]

    if len(set(signatures)) == 1:

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
            return f"{len(sets)} × {reps}"

    pieces = []

    for item in sets:

        reps = item.get(
            "target_reps"
        )

        weight = item.get(
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


def prescribed_set_text(item):

    reps = item.get(
        "target_reps"
    )

    weight = item.get(
        "target_weight_kg"
    )

    if (
        reps is not None
        and weight is not None
    ):
        return (
            f"{reps}×"
            f"{format_weight(weight)}"
        )

    if reps is not None:
        return f"{reps} reps"

    if weight is not None:
        return (
            f"{format_weight(weight)}kg"
        )

    return "—"


def common_reps(sets):

    if not sets:
        return "—"

    reps = [
        item.get("target_reps")
        for item in sets
        if item.get("target_reps")
        is not None
    ]

    if not reps:
        return "—"

    if len(set(reps)) == 1:
        return str(reps[0])

    return "VAR."


def completed_sets(item):

    we_id = (
        item["workout_exercise"]["id"]
    )

    completed = 0

    for set_item in item["sets"]:

        key = get_set_key(
            we_id,
            set_item["set_number"],
            "done",
        )

        if st.session_state.get(
            key,
            False,
        ):
            completed += 1

    extra_count = st.session_state.get(
        f"extra_count_{we_id}",
        0,
    )

    for index in range(extra_count):

        key = get_set_key(
            we_id,
            f"extra_{index + 1}",
            "done",
        )

        if st.session_state.get(
            key,
            False,
        ):
            completed += 1

    return completed


def total_sets(item):

    we_id = (
        item["workout_exercise"]["id"]
    )

    extra_count = st.session_state.get(
        f"extra_count_{we_id}",
        0,
    )

    return (
        len(item["sets"])
        + extra_count
    )


def exercise_status(item):

    done = completed_sets(item)
    total = total_sets(item)

    if total > 0 and done >= total:
        return "COMPLETATO"

    if done > 0:
        return "IN CORSO"

    return "DA FARE"


def total_progress():

    total = 0
    done = 0

    for item in DATA["exercises"]:

        total += total_sets(item)
        done += completed_sets(item)

    if total == 0:
        return 0

    return round(
        done / total * 100
    )


def find_exercise(we_id):

    for item in DATA["exercises"]:

        if (
            item["workout_exercise"]["id"]
            == we_id
        ):
            return item

    return None


def open_exercise(we_id):

    st.session_state.selected_exercise = (
        we_id
    )

    st.session_state.training_started = True

    st.session_state.screen = (
        "exercise"
    )

    st.rerun()


# ============================================================
# BOTTOM NAV
# ============================================================

def bottom_nav(active="today"):

    items = [
        ("⌂", "Oggi", "today"),
        ("▤", "Programma", "program"),
        ("▥", "Progressi", "progress"),
        ("○", "Profilo", "profile"),
    ]

    output = (
        '<div class="bottom-nav">'
    )

    for icon, label, key in items:

        active_class = (
            "bottom-nav-active"
            if active == key
            else ""
        )

        output += (
            f'<div class="bottom-nav-item '
            f'{active_class}">'

            f'<div class="bottom-nav-icon">'
            f'{icon}'
            '</div>'

            f'<div class="bottom-nav-label">'
            f'{label}'
            '</div>'

            '</div>'
        )

    output += "</div>"

    st.markdown(
        output,
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

    initial = (
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

    st.markdown(
        (
            '<div class="app-top">'

            '<div class="logo">'
            'TRAINING '
            '<span class="logo-red">'
            'HUB'
            '</span>'
            '</div>'

            f'<div class="avatar">'
            f'{initial}'
            '</div>'

            '</div>'
        ),
        unsafe_allow_html=True,
    )

    st.markdown(
        (
            f'<div class="hello">'
            f'Ciao, {first_name} 👋'
            '</div>'

            f'<div class="program-name">'
            f'{program_name}'
            '</div>'
        ),
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

    st.markdown(
        (
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
        ),
        unsafe_allow_html=True,
    )

    label = (
        "▶ CONTINUA ALLENAMENTO"
        if st.session_state.training_started
        else "▶ INIZIA ALLENAMENTO"
    )

    if st.button(
        label,
        type="primary",
        use_container_width=True,
        key="home_start",
    ):

        st.session_state.training_started = True

        go("workout")

    st.markdown(
        (
            '<div class="section-title">'
            'IL TUO PROGRAMMA'
            '</div>'
        ),
        unsafe_allow_html=True,
    )

    st.markdown(
        (
            '<div style="'
            'background:#14171c;'
            'border:1px solid #292e35;'
            'border-radius:17px;'
            'padding:15px;'
            '">'

            '<div style="'
            'font-size:16px;'
            'font-weight:900;'
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
        ),
        unsafe_allow_html=True,
    )

    bottom_nav("today")


# ============================================================
# WORKOUT CARD
# ============================================================

def render_exercise_card(item):

    exercise = item["exercise"]
    we = item["workout_exercise"]

    name = exercise.get(
        "name",
        "Esercizio",
    )

    code = (
        we.get("exercise_code")
        or ""
    )

    prescription = prescription_text(
        item["sets"]
    )

    completed = completed_sets(item)
    total = total_sets(item)

    status = exercise_status(item)

    rest = (
        we.get(
            "default_rest_seconds"
        )
        or "—"
    )

    label = (
        f"{code}   {name}\n"
        f"{prescription}\n"
        f"{completed}/{total} serie"
        f"  •  ⏱ {rest}s"
        f"  •  {status}"
    )

    if st.button(
        label,
        key=f"exercise_card_{we['id']}",
        use_container_width=True,
    ):

        open_exercise(
            we["id"]
        )


# ============================================================
# WORKOUT SCREEN
# ============================================================

def render_workout():

    workout = DATA["workout"]

    workout_name = safe(
        workout.get(
            "name",
            "Allenamento",
        )
    )

    back_col, title_col = st.columns(
        [0.18, 0.82]
    )

    with back_col:

        if st.button(
            "‹",
            key="back_home",
        ):
            go("home")

    with title_col:

        st.markdown(
            (
                '<div style="'
                'font-size:22px;'
                'font-weight:900;'
                'padding-top:7px;'
                '">'
                f'{workout_name}'
                '</div>'
            ),
            unsafe_allow_html=True,
        )

    progress = total_progress()

    st.markdown(
        (
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
        ),
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
            [],
        ).append(item)

    for block in DATA["blocks"]:

        items = grouped.get(
            block["id"],
            [],
        )

        if not items:
            continue

        st.markdown(
            (
                '<div class="section-title">'
                f'{safe(block.get("name", "Blocco"))}'
                '</div>'
            ),
            unsafe_allow_html=True,
        )

        for item in items:
            render_exercise_card(item)

    ungrouped = grouped.get(
        None,
        [],
    )

    if ungrouped:

        st.markdown(
            (
                '<div class="section-title">'
                'ALTRI ESERCIZI'
                '</div>'
            ),
            unsafe_allow_html=True,
        )

        for item in ungrouped:
            render_exercise_card(item)

    bottom_nav("today")


# ============================================================
# SET ROW
# ============================================================

def render_set_row(
    we_id,
    set_number,
    prescribed_text,
    default_weight,
    default_reps,
    extra=False,
):

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
        st.session_state[kg_key] = float(
            default_weight or 0
        )

    if reps_key not in st.session_state:
        st.session_state[reps_key] = int(
            default_reps or 0
        )

    with st.container(
        key=f"setrow_{we_id}_{set_number}"
    ):

        cols = st.columns(
            [0.55, 0.9, 1.5, 1.35, 0.48],
            gap=None,
            vertical_alignment="center",
        )

        with cols[0]:

            extra_class = (
                " extra-set-number"
                if extra
                else ""
            )

            display_number = (
                "+"
                if extra
                else str(set_number)
            )

            st.markdown(
                (
                    f'<div class="set-number-box'
                    f'{extra_class}">'
                    f'{safe(display_number)}'
                    '</div>'
                ),
                unsafe_allow_html=True,
            )

        with cols[1]:

            extra_class = (
                " extra-label"
                if extra
                else ""
            )

            st.markdown(
                (
                    f'<div class="set-prescription'
                    f'{extra_class}">'
                    f'{safe(prescribed_text)}'
                    '</div>'
                ),
                unsafe_allow_html=True,
            )

        with cols[2]:

            st.number_input(
                "KG",
                min_value=0.0,
                step=2.5,
                key=kg_key,
                label_visibility="collapsed",
            )

        with cols[3]:

            st.number_input(
                "REPS",
                min_value=0,
                step=1,
                key=reps_key,
                label_visibility="collapsed",
            )

        with cols[4]:

            st.checkbox(
                "✓",
                key=done_key,
                label_visibility="collapsed",
            )


# ============================================================
# EXERCISE SCREEN
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
        go("workout")

    exercise = item["exercise"]
    we = item["workout_exercise"]
    sets = item["sets"]

    workout_name = safe(
        DATA["workout"].get(
            "name",
            "Allenamento",
        )
    )

    exercise_name = safe(
        exercise.get(
            "name",
            "Esercizio",
        )
    )

    exercise_code = safe(
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

    # --------------------------------------------
    # TOP
    # --------------------------------------------

    left, right = st.columns(
        [0.78, 0.22]
    )

    with left:

        if st.button(
            f"‹  {workout_name.upper()}",
            key="exercise_back_top",
        ):
            go("workout")

    with right:

        st.markdown(
            (
                '<div class="exercise-code">'
                f'{exercise_code}'
                '</div>'
            ),
            unsafe_allow_html=True,
        )

    # --------------------------------------------
    # TITLE
    # --------------------------------------------

    st.markdown(
        (
            f'<div class="exercise-name">'
            f'{exercise_name}'
            '</div>'

            f'<div class="exercise-category">'
            f'{category}'
            '</div>'
        ),
        unsafe_allow_html=True,
    )

    # --------------------------------------------
    # IMAGE / VIDEO
    # --------------------------------------------

    image_url = exercise.get(
        "image_url"
    )

    video_url = exercise.get(
        "video_url"
    )

    if image_url:

        st.image(
            image_url,
            use_container_width=True,
        )

    else:

        st.markdown(
            (
                '<div class="exercise-media">'

                '<div '
                'class="exercise-media-placeholder">'
                '🏋️'
                '</div>'

                '</div>'
            ),
            unsafe_allow_html=True,
        )

    if video_url:

        st.link_button(
            "▶ GUARDA VIDEO",
            video_url,
            use_container_width=True,
        )

    description = exercise.get(
        "description"
    )

    if description:

        st.markdown(
            (
                '<div class="exercise-description">'
                f'{safe(description)}'
                '</div>'
            ),
            unsafe_allow_html=True,
        )

    # --------------------------------------------
    # STATS
    # --------------------------------------------

    rest_seconds = (
        we.get(
            "default_rest_seconds"
        )
        or 0
    )

    reps_value = common_reps(
        sets
    )

    st.markdown(
        (
            '<div class="exercise-stats">'

            '<div class="exercise-stat">'
            '<div class="exercise-stat-icon">▱</div>'
            '<div>'
            '<div class="exercise-stat-value">'
            f'{len(sets)} SERIE'
            '</div>'
            '<div class="exercise-stat-label">'
            'Totale'
            '</div>'
            '</div>'
            '</div>'

            '<div class="exercise-stat">'
            '<div class="exercise-stat-icon">↔</div>'
            '<div>'
            '<div class="exercise-stat-value">'
            f'{safe(reps_value)} REPS'
            '</div>'
            '<div class="exercise-stat-label">'
            'Prescritte'
            '</div>'
            '</div>'
            '</div>'

            '<div class="exercise-stat">'
            '<div class="exercise-stat-icon">⏱</div>'
            '<div>'
            '<div class="exercise-stat-value">'
            f'{format_rest(rest_seconds)}'
            '</div>'
            '<div class="exercise-stat-label">'
            'Recupero'
            '</div>'
            '</div>'
            '</div>'

            '</div>'
        ),
        unsafe_allow_html=True,
    )

    # --------------------------------------------
    # SET TITLE
    # --------------------------------------------

    completed = completed_sets(item)
    total = total_sets(item)

    st.markdown(
        (
            '<div class="set-title-row">'

            '<div class="set-title">'
            'SERIE'
            '</div>'

            '<div class="set-progress">'
            f'{completed}/{total}'
            '</div>'

            '</div>'
        ),
        unsafe_allow_html=True,
    )

    # --------------------------------------------
    # HEADER
    # --------------------------------------------

    with st.container(
        key=f"set_header_{we_id}"
    ):

        cols = st.columns(
            [0.55, 0.9, 1.5, 1.35, 0.48],
            gap=None,
            vertical_alignment="center",
        )

        names = [
            "SET",
            "PRESCR.",
            "KG",
            "REPS",
            "✓",
        ]

        for col, name in zip(
            cols,
            names,
        ):

            with col:

                st.markdown(
                    (
                        '<div '
                        'class="set-header-cell">'
                        f'{name}'
                        '</div>'
                    ),
                    unsafe_allow_html=True,
                )

    # --------------------------------------------
    # PRESCRIBED SETS
    # --------------------------------------------

    for set_item in sets:

        render_set_row(
            we_id=we_id,
            set_number=set_item[
                "set_number"
            ],
            prescribed_text=(
                prescribed_set_text(
                    set_item
                )
            ),
            default_weight=set_item.get(
                "target_weight_kg"
            ),
            default_reps=set_item.get(
                "target_reps"
            ),
        )

    # --------------------------------------------
    # EXTRA SETS
    # --------------------------------------------

    extra_key = (
        f"extra_count_{we_id}"
    )

    if extra_key not in st.session_state:
        st.session_state[extra_key] = 0

    extra_count = (
        st.session_state[
            extra_key
        ]
    )

    for index in range(
        extra_count
    ):

        render_set_row(
            we_id=we_id,
            set_number=(
                f"extra_{index + 1}"
            ),
            prescribed_text="EXTRA",
            default_weight=0,
            default_reps=0,
            extra=True,
        )

    if st.button(
        "＋ AGGIUNGI SERIE",
        key=f"add_set_{we_id}",
        use_container_width=True,
    ):

        st.session_state[
            extra_key
        ] += 1

        st.rerun()

    # --------------------------------------------
    # REST
    # --------------------------------------------

    if rest_seconds:

        st.markdown(
            (
                '<div class="rest-panel">'

                '<div class="rest-left">'
                '⏱ RECUPERO'
                '</div>'

                '<div class="rest-clock">'
                f'{format_rest(rest_seconds)}'
                '</div>'

                '<div class="rest-actions">'

                '<div class="rest-mini">'
                '-15s'
                '</div>'

                '<div class="rest-play">'
                '▶'
                '</div>'

                '<div class="rest-mini">'
                '+15s'
                '</div>'

                '</div>'

                '</div>'
            ),
            unsafe_allow_html=True,
        )

    # --------------------------------------------
    # COACH NOTE
    # --------------------------------------------

    coach_notes = we.get(
        "coach_notes"
    )

    if coach_notes:

        st.markdown(
            (
                '<div class="coach-note">'

                '<div class="coach-note-title">'
                '🏷 NOTA COACH'
                '</div>'

                '<div class="coach-note-text">'
                f'{safe(coach_notes)}'
                '</div>'

                '</div>'
            ),
            unsafe_allow_html=True,
        )

    # --------------------------------------------
    # NEXT EXERCISE
    # --------------------------------------------

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

    st.write("")

    if (
        current_index is not None
        and current_index
        < len(DATA["exercises"]) - 1
    ):

        next_item = DATA[
            "exercises"
        ][current_index + 1]

        next_name = next_item[
            "exercise"
        ]["name"]

        next_id = next_item[
            "workout_exercise"
        ]["id"]

        nav_left, nav_right = st.columns(
            [0.42, 0.58]
        )

        with nav_left:

            if st.button(
                "‹ ESERCIZI",
                key=f"all_{we_id}",
            ):
                go("workout")

        with nav_right:

            if st.button(
                (
                    "PROSSIMO: "
                    f"{next_name.upper()} ›"
                ),
                type="primary",
                key=f"next_{we_id}",
            ):

                open_exercise(
                    next_id
                )

    else:

        if st.button(
            "‹ TUTTI GLI ESERCIZI",
            key=f"all_{we_id}",
            use_container_width=True,
        ):
            go("workout")

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
