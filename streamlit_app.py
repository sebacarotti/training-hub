import streamlit as st
import re
import base64
import mimetypes
import streamlit.components.v1 as components
import requests
import html
from pathlib import Path

# ============================================================
# TRAINING HUB V10.1 RESPONSIVE
# IMMAGINI + TABELLA SEMPLIFICATA
# SERIE | RIPETIZIONI | CARICO | ✓
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

BASE_DIR = Path(__file__).resolve().parent
IMAGES_DIR = BASE_DIR


# ============================================================
# MAPPA IMMAGINI
# ============================================================

EXERCISE_IMAGES = {
    "dead bug": "dead_bug.png",
    "pallof press": "pallof_press.png",
    "front squat": "front_squat.png",
    "romanian deadlift": "romanian_deadlift.png",
    "bulgarian split squat": "bulgarian_split_squat.png",
    "nordic hamstring": "nordic_hamstring.png",
    "standing calf raise": "standing_calf_raise.png",

    # esercizi futuri già pronti
    "trazioni alla sbarra": "trazioni_alla_sbarra.png",
    "pull up": "trazioni_alla_sbarra.png",
    "pull-up": "trazioni_alla_sbarra.png",
    "lat pull down": "lat_pull_down.png",
    "lat pulldown": "lat_pull_down.png",
    "rematore con bilanciere": "rematore_con_bilanciere.png",
    "panca piana manubri": "panca_piana_manubri.png",
    "panca manubri": "panca_piana_manubri.png",
    "spinte militari": "spinte_militari.png",
    "military press": "spinte_militari.png",
    "dip alle parallele": "dip_alle_parallele.png",
    "dip": "dip_alle_parallele.png",
    "pull over": "pull_over.png",
    "pullover": "pull_over.png",
    "push up": "push_up.png",
    "push-up": "push_up.png",
    "sumo squat": "sumo_squat.png",
    "hip thrust": "hip_thrust.png",
    "step up": "step_up.png",
    "step-up": "step_up.png",
    "abduzione cavo": "abduzione_cavo.png",
    "abduzione al cavo": "abduzione_cavo.png",
    "plank": "plank.png",
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
        sets_by_we.setdefault(we_id, []).append(set_item)

    exercise_data = []

    for we in workout_exercises:

        exercise = exercises_by_id.get(we["exercise_id"])

        if not exercise:
            continue

        exercise_data.append(
            {
                "workout_exercise": we,
                "exercise": exercise,
                "sets": sets_by_we.get(we["id"], []),
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


/* ============================================================
   BUTTONS
============================================================ */

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


/* ============================================================
   HOME
============================================================ */

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


/* ============================================================
   HERO
============================================================ */

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


/* ============================================================
   PROGRESS
============================================================ */

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


/* ============================================================
   TITLES
============================================================ */

.section-title {
    margin-top: 26px;
    margin-bottom: 10px;

    color: #858d98;

    font-size: 11px;
    font-weight: 900;
    letter-spacing: 1.6px;

    text-transform: uppercase;
}


/* ============================================================
   WORKOUT CARDS
============================================================ */

div[class*="st-key-exercise_card_"] button {
    width: 100%;
    min-height: 72px;

    position: relative;

    padding: 8px 38px 8px 12px;

    overflow: hidden;

    border-radius: 18px;
    border: 1px solid #2c3138;

    background: #14171c;

    color: white;

    text-align: left;
    justify-content: flex-start;
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


/* ============================================================
   EXERCISE DETAIL
============================================================ */

.exercise-code {
    width: 64px;
    height: 38px;
    margin-left: auto;
    padding: 0 10px;

    display: flex;
    align-items: center;
    justify-content: center;

    border-radius: 12px;
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
    margin-top: 3px;
    margin-bottom: 1px;

    color: white;

    font-size: 29px;
    font-weight: 950;
    line-height: 1.05;
}

.exercise-category {
    margin-bottom: 8px;

    color: #8c949f;
    font-size: 14px;
}


/* ============================================================
   EXERCISE IMAGE
============================================================ */

.exercise-image-wrap {
    width: 100%;

    margin-top: 4px;
    margin-bottom: 12px;

    padding: 5px;

    overflow: hidden;

    border-radius: 22px;
    border: 1px solid #303640;

    background:
        linear-gradient(
            145deg,
            #191d22,
            #0d1013
        );
}

.exercise-image-wrap img {
    width: 100%;
    display: block;

    border-radius: 17px;

    object-fit: cover;
}

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
    color: #727b86;
    font-size: 13px;
    font-weight: 800;
}


/* V9.4 - compact square exercise preview */
div[class*="st-key-exercise_image_"] {
    width: 138px;
    height: 138px;
    margin: 2px 0 6px 0;
    overflow: hidden;
    border-radius: 15px;
    border: 1px solid #303640;
    background: #0d1013;
}

div[class*="st-key-exercise_image_"] [data-testid="stImage"],
div[class*="st-key-exercise_image_"] [data-testid="stImageContainer"] {
    width: 138px !important;
    height: 138px !important;
}

div[class*="st-key-exercise_image_"] img {
    width: 138px !important;
    height: 138px !important;
    object-fit: cover !important;
    object-position: center center !important;
    display: block !important;
    margin: 0 !important;
}

/* Small thumbnail in workout exercise list */
div[class*="st-key-workout_thumb_"] {
    width: 62px;
    height: 62px;
    margin: 0;
    overflow: hidden;
    border-radius: 12px;
    border: 1px solid #303640;
    background: #0d1013;
}

div[class*="st-key-workout_thumb_"] [data-testid="stImage"],
div[class*="st-key-workout_thumb_"] [data-testid="stImageContainer"] {
    width: 62px !important;
    height: 62px !important;
}

div[class*="st-key-workout_thumb_"] img {
    width: 62px !important;
    height: 62px !important;
    object-fit: cover !important;
    object-position: center center !important;
    display: block !important;
    margin: 0 !important;
}

.exercise-description {
    margin-top: 9px;
    margin-bottom: 23px;

    color: #a5acb5;

    font-size: 12px;
    line-height: 1.45;
}


/* ============================================================
   SERIES TITLE
============================================================ */

.set-title-row {
    display: flex;
    align-items: center;
    justify-content: space-between;

    margin-top: 10px;
    margin-bottom: 13px;
}

.set-title {
    color: #f2f4f7;

    font-size: 15px;
    font-weight: 950;
    letter-spacing: 1px;
}

.set-progress {
    color: #ff464e;

    font-size: 12px;
    font-weight: 950;
}


/* ============================================================
   TABLE
   SERIE | RIPETIZIONI | CARICO | ✓
============================================================ */

div[class*="st-key-set_header_"] {
    width: 100% !important;
    max-width: 100% !important;

    min-height: 35px !important;

    margin-bottom: 7px !important;
    padding: 0 5px !important;

    overflow: visible !important;
}

div[class*="st-key-setrow_"] {
    width: 100% !important;
    max-width: 100% !important;

    margin-bottom: 7px;
    padding: 6px;

    overflow: hidden !important;

    border-radius: 15px;
    border: 1px solid #262c34;

    background:
        linear-gradient(
            145deg,
            #12161b,
            #0e1115
        );
}

div[class*="st-key-set_header_"]
[data-testid="stHorizontalBlock"],

div[class*="st-key-setrow_"]
[data-testid="stHorizontalBlock"] {

    width: 100% !important;
    max-width: 100% !important;

    display: grid !important;

    grid-template-columns:
        48px
        minmax(0, 1fr)
        minmax(0, 1fr)
        34px !important;

    gap: 7px !important;

    align-items: center !important;
}

div[class*="st-key-set_header_"]
[data-testid="column"],

div[class*="st-key-setrow_"]
[data-testid="column"] {

    width: 100% !important;
    min-width: 0 !important;
    max-width: 100% !important;

    flex: none !important;
}


/* HEADER */

div[class*="st-key-set_header_"]
[data-testid="stHorizontalBlock"] {

    min-height: 35px !important;
    overflow: visible !important;
}

div[class*="st-key-set_header_"]
[data-testid="stMarkdownContainer"] {

    min-height: 35px !important;

    display: flex !important;
    align-items: center !important;
    justify-content: center !important;

    overflow: visible !important;
}

div[class*="st-key-set_header_"] p {
    margin: 0 !important;
    padding: 0 !important;
}

.set-header-cell {
    width: 100%;
    min-height: 35px;

    display: flex;
    align-items: center;
    justify-content: center;

    color: #9da6b2 !important;

    font-size: 9px !important;
    font-weight: 950 !important;

    line-height: 1 !important;

    letter-spacing: .25px;

    white-space: nowrap !important;

    text-align: center;
}


/* ============================================================
   SET ROW
============================================================ */

.set-number-box {
    width: 100%;
    height: 42px;

    display: flex;
    align-items: center;
    justify-content: center;

    border-radius: 10px;

    background: #1b2026;

    color: white;

    font-size: 12px;
    font-weight: 950;
}

.extra-set-number {
    background: #43191e;
    color: #ff5058;
}


/* ============================================================
   NUMBER INPUT
============================================================ */

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

    height: 42px !important;
    min-height: 42px !important;

    padding: 0 21px !important;

    border-radius: 10px !important;

    text-align: center !important;

    font-size: 11px !important;
    font-weight: 950 !important;
}

div[class*="st-key-setrow_"]
[data-testid="stNumberInput"] button {

    width: 20px !important;
    min-width: 20px !important;

    height: 42px !important;

    padding: 0 !important;
}


/* ============================================================
   CHECKBOX
============================================================ */

div[class*="st-key-setrow_"]
[data-testid="stCheckbox"] {

    min-height: 42px !important;

    display: flex !important;

    align-items: center !important;
    justify-content: center !important;

    margin: 0 !important;
}

div[class*="st-key-setrow_"]
[data-testid="stCheckbox"] label {
    padding: 0 !important;
}


/* ============================================================
   ADD SET
============================================================ */

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


/* ============================================================
   REST
============================================================ */

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


/* ============================================================
   COACH NOTE
============================================================ */

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


/* ============================================================
   BOTTOM NAV
============================================================ */

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


/* ============================================================
   MOBILE
============================================================ */

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
        margin-top: 1px;
        font-size: 25px;
        line-height: 1.05;
    }

    .exercise-category {
        margin-top: 2px;
        margin-bottom: 5px;
        font-size: 12px;
    }

    .exercise-code {
        width: 58px;
        height: 34px;
        padding: 0 8px;
        border-radius: 11px;
        font-size: 12px;
    }

    div[class*="st-key-exercise_image_"] {
        width: 92px;
        height: 92px;
        margin: 0 0 4px 0;
        border-radius: 12px;
    }

    div[class*="st-key-exercise_image_"] [data-testid="stImage"],
    div[class*="st-key-exercise_image_"] [data-testid="stImageContainer"],
    div[class*="st-key-exercise_image_"] img {
        width: 92px !important;
        height: 92px !important;
    }

    div[class*="st-key-workout_thumb_"] {
        width: 54px;
        height: 54px;
        border-radius: 10px;
    }

    div[class*="st-key-workout_thumb_"] [data-testid="stImage"],
    div[class*="st-key-workout_thumb_"] [data-testid="stImageContainer"],
    div[class*="st-key-workout_thumb_"] img {
        width: 54px !important;
        height: 54px !important;
    }

    .exercise-description {
        margin-top: 4px;
        margin-bottom: 8px;
        font-size: 11px;
        line-height: 1.3;
    }

    .set-title-row {
        margin-top: 2px;
        margin-bottom: 4px;
    }

    .set-title {
        font-size: 13px;
    }

    div[class*="st-key-set_header_"] {
        min-height: 25px !important;
        margin-bottom: 3px !important;
    }

    .set-header-cell {
        min-height: 25px !important;
        font-size: 7px !important;
    }

    div[class*="st-key-setrow_"] {
        margin-bottom: 4px !important;
        padding: 3px !important;
    }

    .set-number-box {
        height: 30px;
    }

    div[class*="st-key-setrow_"] [data-testid="stNumberInput"] input {
        height: 30px !important;
        min-height: 30px !important;
    }

    div[class*="st-key-setrow_"] [data-testid="stNumberInput"] button {
        height: 30px !important;
    }

    div[class*="st-key-setrow_"] [data-testid="stCheckbox"] {
        min-height: 30px !important;
    }

    div[class*="st-key-set_header_"]
    [data-testid="stHorizontalBlock"],

    div[class*="st-key-setrow_"]
    [data-testid="stHorizontalBlock"] {

        display: grid !important;

        grid-template-columns:
            42px
            minmax(0, 1fr)
            minmax(0, 1fr)
            30px !important;

        gap: 5px !important;

        width: 100% !important;
        max-width: 100% !important;

        overflow: visible !important;
    }

    div[class*="st-key-setrow_"] {

        width: 100% !important;

        padding: 5px !important;

        margin-bottom: 6px;

        overflow: hidden !important;
    }

    div[class*="st-key-set_header_"] {

        min-height: 34px !important;

        margin-bottom: 7px !important;

        padding: 0 5px !important;

        overflow: visible !important;
    }

    .set-header-cell {

        min-height: 34px !important;

        color: #b9c1cc !important;

        font-size: 8px !important;
        font-weight: 950 !important;

        letter-spacing: 0 !important;
    }

    .set-number-box {

        height: 40px;

        font-size: 11px;
    }

    div[class*="st-key-setrow_"]
    [data-testid="stNumberInput"] input {

        height: 40px !important;
        min-height: 40px !important;

        padding: 0 18px !important;

        font-size: 10px !important;
    }

    div[class*="st-key-setrow_"]
    [data-testid="stNumberInput"] button {

        width: 18px !important;
        min-width: 18px !important;

        height: 40px !important;
    }

    div[class*="st-key-setrow_"]
    [data-testid="stCheckbox"] {

        min-height: 40px !important;
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


def image_data_uri(path):
    """Convert a local exercise image to a data URI for compact HTML cards."""
    if not path:
        return ""
    try:
        p = Path(path)
        if not p.exists():
            return ""
        mime = mimetypes.guess_type(str(p))[0] or "image/png"
        encoded = base64.b64encode(p.read_bytes()).decode("ascii")
        return f"data:{mime};base64,{encoded}"
    except Exception:
        return ""


def display_exercise_name(name):
    """Human-facing exercise name: no A1/A2/B1/B2/C1 codes."""
    if not name:
        return ""
    return re.sub(r"^[A-Z]\d+\s*[-–—:]?\s*", "", str(name)).strip()

def safe(value):

    if value is None:
        return ""

    return html.escape(str(value))



def reset_scroll_top():
    """Force Streamlit's page container back to the top after exercise navigation."""
    components.html(
        """
        <script>
        (function () {
            function goTop() {
                try {
                    window.parent.scrollTo(0, 0);
                } catch (e) {}

                try {
                    const doc = window.parent.document;
                    const selectors = [
                        '[data-testid="stAppViewContainer"]',
                        '[data-testid="stMain"]',
                        'section.main',
                        '.main'
                    ];

                    selectors.forEach((selector) => {
                        const el = doc.querySelector(selector);
                        if (el) {
                            el.scrollTop = 0;
                            if (typeof el.scrollTo === 'function') {
                                el.scrollTo({top: 0, left: 0, behavior: 'instant'});
                            }
                        }
                    });
                } catch (e) {}
            }

            goTop();
            setTimeout(goTop, 50);
            setTimeout(goTop, 180);
        })();
        </script>
        """,
        height=0,
        width=0,
    )

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


def get_exercise_image(exercise_name):

    if not exercise_name:
        return None

    name = exercise_name.strip().lower()

    filename = EXERCISE_IMAGES.get(name)

    if not filename:
        return None

    image_path = IMAGES_DIR / filename

    if image_path.exists():
        return image_path

    return None


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

        reps = sets[0].get("target_reps")
        weight = sets[0].get("target_weight_kg")

        if reps is not None and weight is not None:

            return (
                f"{len(sets)} × {reps} "
                f"@ {format_weight(weight)} kg"
            )

        if reps is not None:

            return f"{len(sets)} × {reps}"

    pieces = []

    for item in sets:

        reps = item.get("target_reps")
        weight = item.get("target_weight_kg")

        if reps is not None and weight is not None:

            pieces.append(
                f"{reps}×{format_weight(weight)}kg"
            )

        elif reps is not None:

            pieces.append(f"{reps} reps")

    return " • ".join(pieces)


def completed_sets(item):

    we_id = item["workout_exercise"]["id"]

    completed = 0

    for set_item in item["sets"]:

        key = get_set_key(
            we_id,
            set_item["set_number"],
            "done",
        )

        if st.session_state.get(key, False):
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

        if st.session_state.get(key, False):
            completed += 1

    return completed


def total_sets(item):

    we_id = item["workout_exercise"]["id"]

    extra_count = st.session_state.get(
        f"extra_count_{we_id}",
        0,
    )

    return len(item["sets"]) + extra_count


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

    return round(done / total * 100)


def find_exercise(we_id):

    for item in DATA["exercises"]:

        if item["workout_exercise"]["id"] == we_id:
            return item

    return None


def open_exercise(we_id):

    st.session_state.selected_exercise = we_id
    st.session_state.training_started = True
    st.session_state.screen = "exercise"
    st.session_state.reset_exercise_scroll = True

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

    output = '<div class="bottom-nav">'

    for icon, label, key in items:

        active_class = (
            "bottom-nav-active"
            if active == key
            else ""
        )

        output += (
            f'<div class="bottom-nav-item {active_class}">'
            f'<div class="bottom-nav-icon">{icon}</div>'
            f'<div class="bottom-nav-label">{label}</div>'
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
        athlete.get("first_name", "Atleta")
    )

    initial = (
        first_name[0].upper()
        if first_name
        else "A"
    )

    program_name = safe(
        program.get("name", "Programma")
    )

    workout_name = safe(
        workout.get("name", "Allenamento")
    )

    st.markdown(
        (
            '<div class="app-top">'
            '<div class="logo">'
            'TRAINING '
            '<span class="logo-red">HUB</span>'
            '</div>'
            f'<div class="avatar">{initial}</div>'
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

    exercise_count = len(DATA["exercises"])
    block_count = len(DATA["blocks"])

    minutes = (
        workout.get("estimated_minutes")
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
            f'<div class="stat-number">{exercise_count}</div>'
            '<div class="stat-label">Esercizi</div>'
            '</div>'

            '<div class="stat">'
            f'<div class="stat-number">{minutes}′</div>'
            '<div class="stat-label">Durata</div>'
            '</div>'

            '<div class="stat">'
            f'<div class="stat-number">{block_count}</div>'
            '<div class="stat-label">Blocchi</div>'
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
        '<div class="section-title">IL TUO PROGRAMMA</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        (
            '<div style="'
            'background:#14171c;'
            'border:1px solid #292e35;'
            'border-radius:17px;'
            'padding:15px;">'

            '<div style="'
            'font-size:16px;'
            'font-weight:900;">'
            f'{program_name}'
            '</div>'

            '<div style="'
            'font-size:12px;'
            'color:#9299a4;'
            'margin-top:4px;">'
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

    raw_name = exercise.get("name", "Esercizio")
    name = display_exercise_name(raw_name)

    prescription = prescription_text(item["sets"])
    completed = completed_sets(item)
    total = total_sets(item)
    status = exercise_status(item)
    rest = we.get("default_rest_seconds") or "—"

    label = (
        f"{name}\n"
        f"{prescription}\n"
        f"{completed}/{total} serie  •  ⏱ {rest}s  •  {status}"
    )

    thumb_path = get_exercise_image(raw_name)
    thumb_uri = image_data_uri(thumb_path)

    if thumb_uri:
        st.markdown(
            f"""
            <style>
            div.st-key-exercise_card_{we['id']} button {{
                background-image: url("{thumb_uri}") !important;
                background-repeat: no-repeat !important;
                background-size: 58px 58px !important;
                background-position: 12px center !important;
                padding-left: 84px !important;
                min-height: 76px !important;
            }}
            @media (max-width: 700px) {{
                div.st-key-exercise_card_{we['id']} button {{
                    background-size: 52px 52px !important;
                    background-position: 10px center !important;
                    padding-left: 72px !important;
                    padding-right: 30px !important;
                    min-height: 70px !important;
                }}
            }}
            </style>
            """,
            unsafe_allow_html=True,
        )

    if st.button(
        label,
        key=f"exercise_card_{we['id']}",
        use_container_width=True,
    ):
        open_exercise(we["id"])


# ============================================================
# WORKOUT
# ============================================================

def render_workout():

    workout = DATA["workout"]

    workout_name = safe(
        workout.get("name", "Allenamento")
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
                'padding-top:7px;">'
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
            'margin-top:8px;">'

            f'<span>{len(DATA["exercises"])} esercizi</span>'
            f'<span>{progress}% completato</span>'

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
            item["workout_exercise"].get("block_id")
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

    ungrouped = grouped.get(None, [])

    if ungrouped:

        st.markdown(
            '<div class="section-title">ALTRI ESERCIZI</div>',
            unsafe_allow_html=True,
        )

        for item in ungrouped:
            render_exercise_card(item)

    bottom_nav("today")


# ============================================================
# SET ROW
# SERIE | RIPETIZIONI | CARICO | ✓
# ============================================================

def render_set_row(
    we_id,
    set_number,
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
            [0.60, 1.55, 1.55, 0.45],
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

            st.number_input(
                "RIPETIZIONI",
                min_value=0,
                step=1,
                key=reps_key,
                label_visibility="collapsed",
            )

        with cols[2]:

            st.number_input(
                "CARICO",
                min_value=0.0,
                step=2.5,
                key=kg_key,
                label_visibility="collapsed",
            )

        with cols[3]:

            st.checkbox(
                "✓",
                key=done_key,
                label_visibility="collapsed",
            )


# ============================================================
# EXERCISE
# ============================================================

def render_exercise():

    if st.session_state.pop("reset_exercise_scroll", False):
        reset_scroll_top()


    we_id = st.session_state.selected_exercise

    item = find_exercise(we_id)

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

    raw_exercise_name = exercise.get(
        "name",
        "Esercizio",
    )

    exercise_name = safe(
        raw_exercise_name
    )

    category = safe(
        exercise.get("category")
        or ""
    )

    description = exercise.get("description")
    coach_notes = we.get("coach_notes")

    # ========================================================
    # TOP NAVIGATION
    # ========================================================

    if st.button(
        f"‹  {workout_name.upper()}",
        key="exercise_back_top",
    ):
        go("workout")

    # ========================================================
    # COMPACT EXERCISE HERO
    # ========================================================

    local_image = get_exercise_image(raw_exercise_name)
    remote_image = exercise.get("image_url")
    hero_uri = image_data_uri(local_image)

    image_html = ""
    if hero_uri:
        image_html = f'<img class="exercise-hero-img" src="{hero_uri}" alt="{exercise_name}">'
    elif remote_image:
        image_html = f'<img class="exercise-hero-img" src="{safe(remote_image)}" alt="{exercise_name}">'
    else:
        image_html = '<div class="exercise-hero-placeholder">🏋️</div>'

    description_html = ""
    if description:
        description_html = (
            '<div class="exercise-hero-description">'
            f'{safe(description)}'
            '</div>'
        )

    note_html = ""
    if coach_notes:
        note_html = (
            '<div class="exercise-hero-note">'
            '<span>NOTA COACH</span> '
            f'{safe(coach_notes)}'
            '</div>'
        )

    st.markdown(
        (
            '<div class="exercise-hero">'
            f'{image_html}'
            '<div class="exercise-hero-info">'
            f'<div class="exercise-hero-name">{exercise_name}</div>'
            f'<div class="exercise-hero-category">{category}</div>'
            f'{description_html}'
            f'{note_html}'
            '</div>'
            '</div>'
        ),
        unsafe_allow_html=True,
    )

    video_url = exercise.get("video_url")
    if video_url:
        st.link_button(
            "▶ GUARDA VIDEO",
            video_url,
            use_container_width=True,
        )

    # ========================================================
    # SERIES TITLE
    # ========================================================

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

    # ========================================================
    # HEADER
    # ========================================================

    with st.container(
        key=f"set_header_{we_id}"
    ):

        cols = st.columns(
            [0.60, 1.55, 1.55, 0.45],
            gap=None,
            vertical_alignment="center",
        )

        names = [
            "SERIE",
            "RIPETIZIONI",
            "CARICO",
            "✓",
        ]

        for col, name in zip(
            cols,
            names,
        ):

            with col:

                st.markdown(
                    (
                        '<div class="set-header-cell">'
                        f'{name}'
                        '</div>'
                    ),
                    unsafe_allow_html=True,
                )

    # ========================================================
    # PRESCRIBED SETS
    # ========================================================

    for set_item in sets:

        render_set_row(
            we_id=we_id,
            set_number=set_item["set_number"],
            default_weight=set_item.get(
                "target_weight_kg"
            ),
            default_reps=set_item.get(
                "target_reps"
            ),
        )

    # ========================================================
    # EXTRA SETS
    # ========================================================

    extra_key = f"extra_count_{we_id}"

    if extra_key not in st.session_state:
        st.session_state[extra_key] = 0

    extra_count = st.session_state[
        extra_key
    ]

    for index in range(extra_count):

        render_set_row(
            we_id=we_id,
            set_number=f"extra_{index + 1}",
            default_weight=0,
            default_reps=0,
            extra=True,
        )

    if st.button(
        "＋ AGGIUNGI SERIE",
        key=f"add_set_{we_id}",
        use_container_width=True,
    ):

        st.session_state[extra_key] += 1
        st.rerun()

    # ========================================================
    # RECOVERY
    # ========================================================

    rest_seconds = (
        we.get("default_rest_seconds")
        or 0
    )

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

    # ========================================================
    # NEXT EXERCISE
    # ========================================================

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

st.markdown(r'''<style>
/* =========================================================
   V10 MOBILE COMPACT
   ========================================================= */

/* Remove visible exercise-code pills/labels */
div[class*="st-key-exercise_code_"],
.exercise-code,
.exercise-code-pill,
.code-pill {
    display: none !important;
}

/* Workout list: compact integrated row */
div[class*="st-key-workout_thumb_"] {
    width: 58px !important;
    height: 58px !important;
    margin: 0 !important;
    border-radius: 11px !important;
}
div[class*="st-key-workout_thumb_"] [data-testid="stImage"],
div[class*="st-key-workout_thumb_"] [data-testid="stImageContainer"],
div[class*="st-key-workout_thumb_"] img {
    width: 58px !important;
    height: 58px !important;
    object-fit: cover !important;
    border-radius: 11px !important;
}

div[class*="st-key-exercise_card_"] button {
    min-height: 66px !important;
    padding-top: 7px !important;
    padding-bottom: 7px !important;
    border-radius: 16px !important;
}

/* Detail: compact square visual */
div[class*="st-key-exercise_image_"] {
    width: 104px !important;
    height: 104px !important;
    margin: 0 0 5px 0 !important;
    border-radius: 13px !important;
}
div[class*="st-key-exercise_image_"] [data-testid="stImage"],
div[class*="st-key-exercise_image_"] [data-testid="stImageContainer"],
div[class*="st-key-exercise_image_"] img {
    width: 104px !important;
    height: 104px !important;
    object-fit: cover !important;
    border-radius: 13px !important;
}

.exercise-name {
    font-size: 27px !important;
    line-height: 1.03 !important;
    margin: 1px 0 1px 0 !important;
}
.exercise-category {
    margin: 0 0 4px 0 !important;
    font-size: 12px !important;
}
.exercise-description {
    margin-top: 4px !important;
    margin-bottom: 7px !important;
    font-size: 13px !important;
    line-height: 1.3 !important;
}

/* Sets: denser mobile-app proportions */
div[class*="st-key-setrow_"] {
    margin-bottom: 5px !important;
}
div[class*="st-key-setrow_"] [data-testid="stNumberInput"] input {
    min-height: 30px !important;
    height: 30px !important;
    padding-top: 2px !important;
    padding-bottom: 2px !important;
}
.set-number-box {
    min-height: 30px !important;
    height: 30px !important;
}

/* Recovery card: less vertical space */
.recovery-card,
.recovery-box,
div[class*="recovery"] {
    min-height: 64px !important;
}

/* Mobile */
@media (max-width: 700px) {
    .block-container {
        padding-top: 0.55rem !important;
        padding-bottom: 5.2rem !important;
    }

    div[class*="st-key-workout_thumb_"] {
        width: 52px !important;
        height: 52px !important;
    }
    div[class*="st-key-workout_thumb_"] [data-testid="stImage"],
    div[class*="st-key-workout_thumb_"] [data-testid="stImageContainer"],
    div[class*="st-key-workout_thumb_"] img {
        width: 52px !important;
        height: 52px !important;
    }

    div[class*="st-key-exercise_card_"] button {
        min-height: 60px !important;
        font-size: 13px !important;
    }

    div[class*="st-key-exercise_image_"] {
        width: 86px !important;
        height: 86px !important;
    }
    div[class*="st-key-exercise_image_"] [data-testid="stImage"],
    div[class*="st-key-exercise_image_"] [data-testid="stImageContainer"],
    div[class*="st-key-exercise_image_"] img {
        width: 86px !important;
        height: 86px !important;
    }

    .exercise-name {
        font-size: 24px !important;
    }
    .exercise-description {
        font-size: 12px !important;
        margin-bottom: 5px !important;
    }

    div[class*="st-key-setrow_"] [data-testid="stNumberInput"] input {
        min-height: 28px !important;
        height: 28px !important;
        font-size: 12px !important;
    }
    .set-number-box {
        min-height: 28px !important;
        height: 28px !important;
    }
}
</style>
''' , unsafe_allow_html=True)



st.markdown(
    """
    <style>
    .exercise-code, .exercise-code-pill,
    div[class*="st-key-exercise_code_"] { display: none !important; }

    div[class*="st-key-exercise_card_"] button {
        text-align: left !important;
        white-space: pre-line !important;
        border-radius: 16px !important;
        line-height: 1.35 !important;
        font-size: 14px !important;
    }

    div[class*="st-key-workout_thumb_"] { display: none !important; }

    .exercise-hero {
        display: flex;
        align-items: stretch;
        gap: 14px;
        width: 100%;
        margin: 8px 0 10px 0;
        padding: 10px;
        border: 1px solid #2f353d;
        border-radius: 16px;
        background: #12161b;
        box-sizing: border-box;
    }

    .exercise-hero-img, .exercise-hero-placeholder {
        width: 118px; height: 118px; flex: 0 0 118px;
        border-radius: 12px; object-fit: cover; object-position: center;
        background: #0d1013;
    }

    .exercise-hero-placeholder {
        display:flex; align-items:center; justify-content:center; font-size:28px;
    }

    .exercise-hero-info {
        min-width:0; display:flex; flex-direction:column; justify-content:center;
    }

    .exercise-hero-name {
        color:#fff; font-size:25px; line-height:1.05; font-weight:900; margin-bottom:3px;
    }

    .exercise-hero-category {
        color:#9aa5b2; font-size:12px; margin-bottom:7px;
    }

    .exercise-hero-description {
        color:#c3cad2; font-size:13px; line-height:1.3; margin-bottom:7px;
    }

    .exercise-hero-note {
        color:#d7dce2; font-size:12px; line-height:1.3; padding:6px 8px;
        border-left:3px solid #ff3d49; background:#171b21; border-radius:7px;
    }

    .exercise-hero-note span {
        color:#ff4b55; font-weight:900; font-size:10px; letter-spacing:.08em;
    }

    .set-title-row { margin-top:8px !important; margin-bottom:4px !important; }
    div[class*="st-key-setrow_"] { margin-bottom:4px !important; }

    .rest-panel {
        margin-top:8px !important; margin-bottom:8px !important;
        min-height:64px !important; padding-top:8px !important; padding-bottom:8px !important;
    }

    @media (max-width:700px) {
        .block-container {
            padding-top:.45rem !important; padding-left:1rem !important;
            padding-right:1rem !important; padding-bottom:5.3rem !important;
        }

        div[class*="st-key-exercise_card_"] button {
            min-height:68px !important; font-size:12px !important;
            line-height:1.28 !important; border-radius:15px !important;
        }

        .exercise-hero {
            gap:9px; margin:5px 0 7px 0; padding:7px; border-radius:14px;
        }

        .exercise-hero-img, .exercise-hero-placeholder {
            width:84px; height:84px; flex-basis:84px; border-radius:10px;
        }

        .exercise-hero-name {
            font-size:19px; line-height:1.02; margin-bottom:2px;
        }

        .exercise-hero-category { font-size:10px; margin-bottom:3px; }

        .exercise-hero-description {
            font-size:10.5px; line-height:1.2; margin-bottom:4px;
            display:-webkit-box; -webkit-line-clamp:2;
            -webkit-box-orient:vertical; overflow:hidden;
        }

        .exercise-hero-note {
            font-size:10px; line-height:1.18; padding:4px 6px;
            display:-webkit-box; -webkit-line-clamp:2;
            -webkit-box-orient:vertical; overflow:hidden;
        }

        .exercise-hero-note span { font-size:8px; }

        .set-title-row { margin-top:5px !important; margin-bottom:2px !important; }
        .set-title { font-size:17px !important; }
        .set-header-cell { font-size:8px !important; }

        div[class*="st-key-setrow_"] [data-testid="stNumberInput"] input {
            height:28px !important; min-height:28px !important; font-size:11px !important;
        }

        .set-number-box { height:28px !important; min-height:28px !important; }

        .rest-panel { min-height:56px !important; padding:6px 8px !important; }
        .rest-clock { font-size:22px !important; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

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
