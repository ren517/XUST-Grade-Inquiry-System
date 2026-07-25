import os
import json

USER_DIR = "users"
COOKIE_DIR = "cookies"


def init():

    if not os.path.exists(USER_DIR):
        os.makedirs(USER_DIR)

    if not os.path.exists(COOKIE_DIR):
        os.makedirs(COOKIE_DIR)


# =====================
# 用户管理
# =====================


def load_users():

    init()

    users = []

    for file in os.listdir(USER_DIR):

        if file.endswith(".json"):

            path = os.path.join(USER_DIR, file)

            with open(path, encoding="utf-8") as f:

                users.append(json.load(f))

    return users


def save_user(name, xh, info):

    init()

    user = {"name": name, "xh": xh, **info}

    with open(f"{USER_DIR}/{xh}.json", "w", encoding="utf-8") as f:

        json.dump(user, f, ensure_ascii=False, indent=4)


# =====================
# Cookie管理
# =====================


def save_cookie(session, xh):

    init()

    cookies = session.cookies.get_dict()

    with open(f"{COOKIE_DIR}/{xh}.json", "w", encoding="utf-8") as f:

        json.dump(cookies, f, indent=4)


def load_cookie(session, xh):

    path = f"{COOKIE_DIR}/{xh}.json"

    if not os.path.exists(path):

        return False

    with open(path, encoding="utf-8") as f:

        cookies = json.load(f)

    session.cookies.update(cookies)

    return True


def clear_cookie(xh):

    path = f"{COOKIE_DIR}/{xh}.json"

    if os.path.exists(path):

        os.remove(path)
