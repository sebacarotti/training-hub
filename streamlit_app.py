import streamlit as st
import requests
import html

# ============================================================
# TRAINING HUB V5
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
            [],
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
# LOAD DATA
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

st.markdown(
    """
<style>

/* ==========================================================
   GLOBAL
========================================================== */

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

.stApp {
    background:
        radial-gradient(
            circle at 50% -10%,
            #1b2027 0%,
            #0d1014 32%,
            #07090b 72%
        );
    color: white;
}

.block-container {
    max-width: 620px;
    padding-top: 18px;
    padding-left: 16px;
    padding-right: 16px;
    padding-bottom: 100px;
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


/* ==========================================================
   STANDARD BUTTON
========================================================== */

.stButton > button {
    width: 100%;
    min-height: 44px;

    border-radius: 14px;

    border: 1px solid #303640;

    background: #171b20;

    color: white;

    font-weight: 800;

    transition: all .15s ease;
}

.stButton > button:hover {
    color: white;

    background: #20252c;

    border-color: #ff3d46;
}

.stButton > button[kind="primary"] {
    background:
        linear-gradient(
            135deg,
            #ff3039,
            #ff444c
        );

    border: none;

    color: white;
}


/* ==========================================================
   HEADER HOME
========================================================== */

.app-top {
    display: flex;
    align-items: center;
    justify-content: space-between;

    margin-bottom: 28px;
}

.logo {
    font-size: 18px;
    font-weight: 900;
    letter-spacing: 1px;
}

.logo-red {
    color: #ff3d46;
}

.avatar {
    width: 40px;
    height: 40px;

    border-radius: 50%;

    background: #20242a;

    border: 1px solid #353b44;

    display: flex;
    align-items: center;
    justify-content: center;

    font-weight: 900;
}

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


/* ==========================================================
   HOME HERO
========================================================== */

.hero {
    padding: 22px;

    border-radius: 24px;

    border: 1px solid #303640;

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
    color: #ff5259;

    font-size: 11px;
    font-weight: 900;

    letter-spacing: 1.4px;
}

.hero-title {
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
    font-size: 19px;
    font-weight: 900;
}

.stat-label {
    color: #717985;

    font-size: 9px;
    font-weight: 800;

    text-transform: uppercase;

    margin-top: 2px;
}


/* ==========================================================
   PROGRESS
========================================================== */

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


/* ==========================================================
   SECTION TITLE
========================================================== */

.section-title {
    color: #858d98;

    font-size: 11px;
    font-weight: 900;

    letter-spacing: 1.6px;

    text-transform: uppercase;

    margin-top: 26px;
    margin-bottom: 10px;
}


/* ==========================================================
   CLICKABLE EXERCISE CARDS
========================================================== */

div[class*="st-key-exercise_card_"] button {
    width: 100%;

    min-height: 98px;

    padding:
        13px
        48px
        13px
        86px;

    position: relative;

    border-radius: 18px;

    border: 1px solid #2c3138;

    background: #14171c;

    color: white;

    text-align: left;

    justify-content: flex-start;

    overflow: hidden;
}

div[class*="st-key-exercise_card_"] button:hover {
    background: #191d22;
    border-color: #414751;
}

div[class*="st-key-exercise_card_"] button::before {
    content: "🏋️";

    position: absolute;

    left: 13px;
    top: 50%;

    transform: translateY(-50%);

    width: 60px;
    height: 60px;

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

    font-size: 24px;
}

div[class*="st-key-exercise_card_"] button::after {
    content: "›";

    position: absolute;

    right: 16px;
    top: 50%;

    transform: translateY(-50%);

    color: #7e8793;

    font-size: 28px;
}

div[class*="st-key-exercise_card_"] button p {
    margin: 0;

    white-space: pre-wrap;

    text-align: left;

    font-size: 13px;

    line-height: 1.45;
}


/* ==========================================================
   EXERCISE TOP
========================================================== */

.exercise-top {
    display: flex;
    align-items: center;
    justify-content: space-between;

    margin-bottom: 18px;
}

.exercise-back {
    color: #dce0e5;

    font-size: 11px;
    font-weight: 900;

    letter-spacing: .7px;
}

.exercise-code {
    min-width: 45px;
    height: 42px;

    padding: 0 12px;

    border-radius: 14px;

    display: flex;
    align-items: center;
    justify-content: center;

    color: white;

    font-size: 13px;
    font-weight: 900;

    background:
        linear-gradient(
            145deg,
            #481b21,
            #2c1519
        );

    border: 1px solid #ff3d46;
}

.exercise-name {
    color: white;

    font-size: 32px;
    font-weight: 950;

    line-height: 1.06;

    margin-bottom: 5px;
}

.exercise-category {
    color: #8c949f;

    font-size: 14px;

    margin-bottom: 15px;
}


/* ==========================================================
   MEDIA
========================================================== */

.exercise-media {
    width: 100%;
    height: 180px;

    border-radius: 21px;

    border: 1px solid #292f37;

    background:
        radial-gradient(
            circle at 50% 35%,
            #242a31,
            #111419 70%
        );

    display: flex;
    align-items: center;
    justify-content: center;

    position: relative;

    overflow: hidden;

    margin-bottom: 11px;
}

.exercise-media-placeholder {
    font-size: 42px;
    opacity: .9;
}

.media-play {
    position: absolute;

    right: 17px;
    bottom: 16px;

    width: 50px;
    height: 50px;

    border-radius: 50%;

    border: 1px solid #404751;

    background: rgba(10,12,15,.86);

    display: flex;
    align-items: center;
    justify-content: center;

    font-size: 18px;
}

.exercise-description {
    color: #a5acb5;

    font-size: 12px;

    line-height: 1.45;

    margin-bottom: 12px;
}


/* ==========================================================
   EXERCISE STATS
========================================================== */

.exercise-stats {
    display: grid;

    grid-template-columns:
        repeat(3, 1fr);

    gap: 7px;

    margin-top: 13px;
    margin-bottom: 24px;
}

.exercise-stat {
    min-height: 66px;

    padding: 10px 8px;

    border-radius: 16px;

    border: 1px solid #292f37;

    background:
        linear-gradient(
            145deg,
            #191d22,
            #111419
        );

    display: flex;

    align-items: center;

    gap: 8px;
}

.exercise-stat-icon {
    width: 33px;
    height: 33px;

    flex: 0 0 33px;

    border-radius: 10px;

    display: flex;
    align-items: center;
    justify-content: center;

    background: #35171c;

    color: #ff4149;

    font-size: 16px;
}

.exercise-stat-value {
    color: white;

    font-size: 13px;
    font-weight: 900;
}

.exercise-stat-label {
    color: #777f8a;

    font-size: 8px;
    font-weight: 800;

    margin-top: 2px;

    text-transform: uppercase;
}


/* ==========================================================
   SET TABLE
========================================================== */

.set-table-title {
    display: flex;
    align-items: center;
    justify-content: space-between;

    margin-top: 10px;
    margin-bottom: 8px;
}

.set-table-title-left {
    color: #858d98;

    font-size: 11px;
    font-weight: 900;

    letter-spacing: 1.6px;
}

.set-header {
    display: grid;

    grid-template-columns:
        36px
        72px
        minmax(76px, 1fr)
        minmax(72px, .85fr)
        28px;

    gap: 5px;

    align-items: center;

    min-height: 35px;

    padding: 0 5px;

    border-radius: 12px;

    background: #13171c;

    color: #747d89;

    font-size: 8px;
    font-weight: 900;

    text-align: center;

    margin-bottom: 6px;
}


/* ==========================================================
   STREAMLIT ROW
========================================================== */

div[class*="st-key-setrow_"] {
    background:
        linear-gradient(
            145deg,
            #12161b,
            #0e1115
        );

    border: 1px solid #20252c;

    border-radius: 14px;

    padding: 7px 6px;

    margin-bottom: 6px;
}


/* ==========================================================
   INPUTS COMPACT
========================================================== */

[data-testid="stNumberInput"] {
    margin: 0 !important;
}

[data-testid="stNumberInput"] label {
    display: none !important;
}

[data-testid="stNumberInput"] > div {
    min-width: 0 !important;
}

[data-testid="stNumberInput"] input {
    min-height: 38px !important;
    height: 38px !important;

    padding-left: 1px !important;
    padding-right: 1px !important;

    text-align: center !important;

    font-size: 12px !important;
    font-weight: 900 !important;
}

[data-testid="stNumberInput"] button {
    min-width: 22px !important;
    width: 22px !important;

    height: 38px !important;

    padding: 0 !important;
}

[data-testid="stCheckbox"] {
    display: flex;

    align-items: center;
    justify-content: center;

    min-height: 38px;

    margin: 0 !important;
}

[data-testid="stCheckbox"] label {
    padding: 0 !important;
}


/* ==========================================================
   ADD SET
========================================================== */

div[class*="st-key-add_set_"] button {
    margin-top: 8px;

    min-height: 47px;

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


/* ==========================================================
   REST PANEL
========================================================== */

.rest-panel {
    margin-top: 17px;

    min-height: 86px;

    padding: 15px;

    border-radius: 18px;

    border: 1px solid #ff3c45;

    background:
        radial-gradient(
            circle at 50% 50%,
            #37181d,
            #181216 70%
        );

    display: flex;
    align-items: center;
    justify-content: space-between;
}

.rest-left {
    color: #ff4c54;

    font-size: 10px;
    font-weight: 900;

    letter-spacing: .8px;
}

.rest-clock {
    color: white;

    font-size: 29px;
    font-weight: 950;

    letter-spacing: 1px;
}

.rest-actions {
    display: flex;

    align-items: center;

    gap: 5px;
}

.rest-mini {
    min-width: 39px;

    height: 37px;

    padding: 0 6px;

    border-radius: 11px;

    background: #252a31;

    border: 1px solid #343a43;

    display: flex;
    align-items: center;
    justify-content: center;

    color: white;

    font-size: 10px;
    font-weight: 900;
}

.rest-play {
    width: 44px;
    height: 44px;

    border-radius: 50%;

    background:
        linear-gradient(
            145deg,
            #ff313b,
            #ff5057
        );

    display: flex;
    align-items: center;
    justify-content: center;

    color: white;

    font-size: 16px;
}


/* ==========================================================
   COACH NOTE
========================================================== */

.coach-note {
    margin-top: 14px;

    padding: 14px 15px;

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
    color: #ff464e;

    font-size: 9px;
    font-weight: 900;

    letter-spacing: 1px;

    margin-bottom: 5px;
}

.coach-note-text {
    color: #abb2bb;

    font-size: 11px;

    line-height: 1.45;
}


/* ==========================================================
   NAVIGATION AREA
========================================================== */

.exercise-nav-space {
    height: 8px;
}


/* ==========================================================
   BOTTOM NAV
========================================================== */

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


/* ==========================================================
   MOBILE
========================================================== */

@media (max-width: 600px) {

    .block-container {
        padding-top: 12px;
        padding-left: 12px;
        padding-right: 12px;
        padding-bottom: 94px;
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

    div[class*="st-key-exercise_card_"] button {
        min-height: 90px;

        padding-left: 77px;
        padding-right: 38px;

        padding-top: 10px;
        padding-bottom: 10px;
    }

    div[class*="st-key-exercise_card_"] button::before {
        width: 53px;
        height: 53px;

        left: 10px;

        font-size: 21px;
    }

    div[class*="st-key-exercise_card_"] button p {
        font-size: 12px;

        line-height: 1.4;
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
        padding: 8px 6px;

        gap: 5px;
    }

    .exercise-stat-icon {
        width: 29px;
        height: 29px;

        flex-basis: 29px;

        font-size: 14px;
    }

    .exercise-stat-value {
        font-size: 11px;
    }

    .exercise-stat-label {
        font-size: 7px;
    }

    .rest-panel {
        padding: 12px 10px;
    }

    .rest-clock {
        font-size: 24px;
    }

    .rest-mini {
        min-width: 34px;

        height: 34px;

        font-size: 9px;
    }

    .rest-play {
        width: 39px;
        height: 39px;
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


def get_set_key(we_id, set_number, field):

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

    if signatures and len(set(signatures)) == 1:

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

    for s in sets:

        reps = s.get("target_reps")
        weight = s.get("target_weight_kg")

        if reps is not None and weight is not None:
            pieces.append(
                f"{reps}×{format_weight(weight)}kg"
            )

        elif reps is not None:
            pieces.append(f"{reps} reps")

    return " • ".join(pieces)


def prescribed_set_text(prescribed_set):

    reps = prescribed_set.get("target_reps")
    weight = prescribed_set.get("target_weight_kg")

    if reps is not None and weight is not None:
        return (
            f"{reps} × "
            f"{format_weight(weight)}"
        )

    if reps is not None:
        return f"{reps} reps"

    if weight is not None:
        return f"{format_weight(weight)} kg"

    return "—"


def completed_sets(item):

    we_id = item["workout_exercise"]["id"]

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

    we_id = item["workout_exercise"]["id"]

    extras = st.session_state.get(
        f"extra_count_{we_id}",
        0,
    )

    return len(item["sets"]) + extras


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

    st.session_state.selected_exercise = we_id
    st.session_state.training_started = True
    st.session_state.screen = "exercise"

    st.rerun()


def format_rest(seconds):

    if not seconds:
        return "00:00"

    minutes = int(seconds) // 60
    seconds = int(seconds) % 60

    return f"{minutes:02d}:{seconds:02d}"


def common_reps(sets):

    if not sets:
        return "—"

    reps = [
        x.get("target_reps")
        for x in sets
        if x.get("target_reps") is not None
    ]

    if not reps:
        return "—"

    if len(set(reps)) == 1:
        return str(reps[0])

    return "VAR."


# ============================================================
# BOTTOM NAV
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
            f'{first_letter}'
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

    if st.session_state.training_started:
        start_label = "▶ CONTINUA ALLENAMENTO"
    else:
        start_label = "▶ INIZIA ALLENAMENTO"

    if st.button(
        start_label,
        type="primary",
        use_container_width=True,
        key="home_start",
    ):

        st.session_state.training_started = True

        go("workout")

    st.markdown(
        '<div class="section-title">'
        'IL TUO PROGRAMMA'
        '</div>',
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

            f'<div style="'
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
# EXERCISE CARD
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

    done = completed_sets(item)
    total = total_sets(item)

    status = exercise_status(item)

    rest = (
        we.get("default_rest_seconds")
        or "—"
    )

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
            render_exercise_card(item)

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
            render_exercise_card(item)

    bottom_nav("today")


# ============================================================
# EXERCISE DETAIL V5
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
        st.session_state.screen = "workout"
        st.rerun()

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

    code = safe(
        we.get("exercise_code")
        or ""
    )

    category = safe(
        exercise.get("category")
        or ""
    )

    # ========================================================
    # TOP NAV
    # ========================================================

    top_left, top_right = st.columns(
        [0.78, 0.22]
    )

    with top_left:

        if st.button(
            f"‹  {workout_name.upper()}",
            key="exercise_back_top",
        ):
            go("workout")

    with top_right:

        st.markdown(
            (
                '<div class="exercise-code">'
                f'{code}'
                '</div>'
            ),
            unsafe_allow_html=True,
        )

    # ========================================================
    # NAME
    # ========================================================

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

    # ========================================================
    # IMAGE / VIDEO
    # ========================================================

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

        play_html = ""

        if video_url:
            play_html = (
                '<div class="media-play">'
                '▶'
                '</div>'
            )

        st.markdown(
            (
                '<div class="exercise-media">'

                '<div class="exercise-media-placeholder">'
                '🏋️'
                '</div>'

                f'{play_html}'

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

    # ========================================================
    # QUICK STATS
    # ========================================================

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
            '<div class="exercise-stat-icon">'
            '▱'
            '</div>'
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
            '<div class="exercise-stat-icon">'
            '↔'
            '</div>'
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
            '<div class="exercise-stat-icon">'
            '⏱'
            '</div>'
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

    # ========================================================
    # SERIES TITLE
    # ========================================================

    st.markdown(
        (
            '<div class="set-table-title">'

            '<div class="set-table-title-left">'
            'SERIE'
            '</div>'

            '</div>'
        ),
        unsafe_allow_html=True,
    )

    # ========================================================
    # TABLE HEADER
    # ========================================================

    header_cols = st.columns(
        [0.48, 0.9, 1.45, 1.25, 0.42],
        gap="small",
    )

    header_names = [
        "SET",
        "PRESCR.",
        "KG",
        "REPS",
        "✓",
    ]

    for col, title in zip(
        header_cols,
        header_names,
    ):

        with col:

            st.markdown(
                (
                    '<div style="'
                    'height:28px;'
                    'display:flex;'
                    'align-items:center;'
                    'justify-content:center;'
                    'color:#747d89;'
                    'font-size:8px;'
                    'font-weight:900;'
                    '">'
                    f'{title}'
                    '</div>'
                ),
                unsafe_allow_html=True,
            )

    # ========================================================
    # PRESCRIBED SETS
    # ========================================================

    for prescribed_set in sets:

        set_number = (
            prescribed_set["set_number"]
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
            st.session_state[kg_key] = weight_default

        if reps_key not in st.session_state:
            st.session_state[reps_key] = reps_default

        prescribed = safe(
            prescribed_set_text(
                prescribed_set
            )
        )

        with st.container(
            key=f"setrow_{we_id}_{set_number}"
        ):

            row = st.columns(
                [
                    0.48,
                    0.90,
                    1.45,
                    1.25,
                    0.42,
                ],
                gap="small",
            )

            with row[0]:

                st.markdown(
                    (
                        '<div style="'
                        'height:38px;'
                        'display:flex;'
                        'align-items:center;'
                        'justify-content:center;'
                        'border-radius:10px;'
                        'background:#1b2026;'
                        'font-size:12px;'
                        'font-weight:900;'
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
                        'height:38px;'
                        'display:flex;'
                        'align-items:center;'
                        'justify-content:center;'
                        'font-size:10px;'
                        'color:#a2a9b2;'
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

    # ========================================================
    # EXTRA SETS
    # ========================================================

    extra_key = (
        f"extra_count_{we_id}"
    )

    if extra_key not in st.session_state:
        st.session_state[extra_key] = 0

    extra_count = st.session_state[
        extra_key
    ]

    for i in range(extra_count):

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

        with st.container(
            key=f"setrow_extra_{we_id}_{i}"
        ):

            row = st.columns(
                [
                    0.48,
                    0.90,
                    1.45,
                    1.25,
                    0.42,
                ],
                gap="small",
            )

            with row[0]:

                st.markdown(
                    (
                        '<div style="'
                        'height:38px;'
                        'display:flex;'
                        'align-items:center;'
                        'justify-content:center;'
                        'border-radius:10px;'
                        'background:#35171c;'
                        'color:#ff5058;'
                        'font-size:11px;'
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
                        'height:38px;'
                        'display:flex;'
                        'align-items:center;'
                        'justify-content:center;'
                        'color:#ff5058;'
                        'font-size:8px;'
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
        use_container_width=True,
    ):

        st.session_state[
            extra_key
        ] += 1

        st.rerun()

    # ========================================================
    # REST VISUAL PANEL
    # Countdown reale lo aggiungiamo dopo
    # ========================================================

    if rest_seconds:

        st.markdown(
            (
                '<div class="rest-panel">'

                '<div class="rest-left">'
                '⏱ RECUPERO'
                '</div>'

                f'<div class="rest-clock">'
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
    # COACH NOTE
    # ========================================================

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

    # ========================================================
    # PREVIOUS / NEXT
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

    st.markdown(
        '<div class="exercise-nav-space"></div>',
        unsafe_allow_html=True,
    )

    if (
        current_index is not None
        and current_index < len(
            DATA["exercises"]
        ) - 1
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
            [0.43, 0.57]
        )

        with nav_left:

            if st.button(
                "‹ TUTTI GLI ESERCIZI",
                key=f"all_exercises_{we_id}",
            ):
                go("workout")

        with nav_right:

            if st.button(
                f"PROSSIMO: {next_name.upper()} ›",
                type="primary",
                key=f"next_{we_id}",
            ):
                open_exercise(next_id)

    else:

        if st.button(
            "‹ TUTTI GLI ESERCIZI",
            key=f"all_exercises_{we_id}",
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
