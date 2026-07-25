import json
import os
from datetime import datetime

HISTORY_DIR = "history"


def get_history_path(xh):

    if not os.path.exists(HISTORY_DIR):
        os.mkdir(HISTORY_DIR)

    return f"{HISTORY_DIR}/{xh}.json"


def load_history(xh):

    path = get_history_path(xh)

    if not os.path.exists(path):
        return None

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_history(xh, name, courses):

    path = get_history_path(xh)

    data = {
        "xh": xh,
        "name": name,
        "update_time": str(datetime.now()),
        "courses": courses,
    }

    with open(path, "w", encoding="utf-8") as f:

        json.dump(data, f, ensure_ascii=False, indent=4)


def compare_courses(old, new):

    old_keys = {x["key"] for x in old}

    new_courses = []

    for course in new:

        if course["key"] not in old_keys:
            new_courses.append(course)

    return new_courses
