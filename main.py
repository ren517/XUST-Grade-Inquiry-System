import sys

from cookie_manager import *
from score import *
from history import *
from login import *
from crypto import *
from ids_login import IdsLogin
from jwsso_login import JwssoLogin

# ======================
# 登录入口
# ======================
# 默认 legacy：老教务系统 RSA 登录，行为与改造前完全一致
# 可选 ids / jwsso：统一认证新入口，只在登录换 cookie 这一步不同

DEFAULT_ENTRY = "legacy"


def get_entry(user):

    entry = user.get("entry") or DEFAULT_ENTRY

    for a in sys.argv[1:]:

        if a.startswith("--entry="):

            entry = a.split("=", 1)[1]

    return entry


def create_client(entry):

    if entry == "ids":

        return IdsLogin()

    if entry == "jwsso":

        return JwssoLogin()

    return JWXTLogin()


users = load_users()


print("===================")
print(" 西科大教务助手")
print("===================")


for i, u in enumerate(users):

    print(i + 1, u["name"], u["xh"])


print("0 添加用户")


choice = input("请选择:")


# ======================
# 添加用户
# ======================

if choice == "0":

    name = input("姓名:")
    xh = input("学号:")
    password = input("教务系统密码:")

    password = encrypt_password(password)

    save_user(name, xh, {"password": password})

    print("用户添加成功")

    exit()


# ======================
# 查询成绩
# ======================

user = users[int(choice) - 1]


print("当前用户:", user["name"])


# 登录入口（legacy 时为空，保持老 cookie 文件名）

entry = get_entry(user)

if entry != DEFAULT_ENTRY:

    print("登录入口:", entry)


# 创建登录对象

login_client = create_client(entry)

cookie_entry = None if entry == DEFAULT_ENTRY else entry


# ======================
# 尝试读取Cookie
# ======================

has_cookie = load_cookie(login_client.session, user["xh"], cookie_entry)


if has_cookie:

    print("检测缓存登录...")

    if login_client.check_login():

        print("Cookie有效")

    else:

        print("Cookie失效，重新登录")

        password = decrypt_password(user["password"])

        success = login_client.login(user["xh"], password)

        if not success:

            print("登录失败")

            exit()

        save_cookie(login_client.session, user["xh"], cookie_entry)


else:

    print("无缓存Cookie，首次登录")

    password = decrypt_password(user["password"])

    success = login_client.login(user["xh"], password)

    if not success:

        print("登录失败")

        exit()

    save_cookie(login_client.session, user["xh"], cookie_entry)


print("登录成功")


# ======================
# 查询成绩
# ======================

result = select_score(login_client.session, user["name"])


if result is None:

    print("成绩查询失败")

    exit()


courses = result["items"]


# ======================
# 成绩变化检测
# ======================

history = load_history(user["xh"])


if history is None:

    print("第一次运行，保存成绩")


else:

    old_courses = history["courses"]

    new = compare_courses(old_courses, courses)

    if new:

        print("================")
        print("发现新增课程:")
        print("================")

        for c in new:

            print(c["kcmc"], "成绩:", c.get("cj"), "学分:", c.get("xf"))

    else:

        print("没有新增成绩")


# ======================
# 更新历史记录
# ======================

save_history(user["xh"], user["name"], courses)
