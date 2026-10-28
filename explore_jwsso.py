"""
jwsso 登录后探索脚本

用途：登录统一用户中心，看登录后的页面里有哪些应用入口，
     定位跳转回教务系统（jwglxt）的那条链接

用法：

    python explore_jwsso.py
"""

import re

from cookie_manager import load_users
from crypto import decrypt_password
from jwsso_login import JwssoLogin, JWSSO_BASE, LOGIN_URL, UA


def main():

    users = load_users()

    if not users:

        print("没有用户，先运行 main.py 添加")

        return

    for i, u in enumerate(users):

        print(i + 1, u["name"], u["xh"], u.get("entry", "legacy"))

    user = users[int(input("选择用户:") or "1") - 1]

    password = input("密码（回车使用已保存的）:")

    if not password:

        password = decrypt_password(user["password"])

    client = JwssoLogin()

    ok = client.login(user["xh"], password)

    print("登录:", ok)

    if not ok:

        return

    print("cookie:", client.session.cookies.get_dict())

    # 登录后的首页
    for path in ("/auth/user/index", "/auth/index", "/auth/oauth/index", "/"):

        try:

            r = client.session.get(JWSSO_BASE + path, headers={"User-Agent": UA}, timeout=15)

            print("================")
            print(path, r.status_code, "len", len(r.text), "final:", r.url)

            if r.status_code != 200:

                continue

            title = re.search(r"<title>(.*?)</title>", r.text, re.S)

            print("title:", title.group(1).strip() if title else "")

            links = client.find_jwglxt_links(r.text)

            print("教务相关链接:", links[:10])

            all_links = re.findall(r'href="([^"]+)"', r.text)

            print("全部链接(前25):", all_links[:25])

            break

        except Exception as e:

            print(path, "ERR", e)

    # 教务系统是否已登录
    print("================")
    print("jwglxt check_login:", client.check_login())
    print("cookie:", client.session.cookies.get_dict())


if __name__ == "__main__":

    main()
