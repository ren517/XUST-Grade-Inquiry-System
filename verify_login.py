"""
新认证入口验证脚本

用途：确认新入口能拿到有效 cookie，并走通后续成绩查询流程

用法：

    python verify_login.py                    # 老入口（作为对照）
    python verify_login.py --entry=ids        # 统一身份认证 CAS
    python verify_login.py --entry=jwsso      # 统一用户中心

可选参数：

    --service=<url>    ids 入口的 CAS 回调地址
    --authorize=<url>  jwsso 入口的票据回传地址

验证通过的标准：

    1.登录返回 True
    2.cookie 中出现 JSESSIONID
    3.check_login() 为 True
    4.select_score() 返回 items 且字段完整
"""

import sys

from cookie_manager import load_users
from crypto import decrypt_password
from login import JWXTLogin
from ids_login import IdsLogin
from jwsso_login import JwssoLogin
from score import select_score


def get_arg(name):

    for a in sys.argv[1:]:

        if a.startswith("--" + name + "="):

            return a.split("=", 1)[1]

    return None


def create_client(entry):

    if entry == "ids":

        return IdsLogin(service=get_arg("service"))

    if entry == "jwsso":

        return JwssoLogin(
            authorize_url=get_arg("authorize"),
            client_id=get_arg("client_id"),
            redirect_uri=get_arg("redirect_uri"),
        )

    return JWXTLogin()


def main():

    entry = get_arg("entry") or "legacy"

    users = load_users()

    if not users:

        print("没有用户，先运行 main.py 添加")

        return

    for i, u in enumerate(users):

        print(i + 1, u["name"], u["xh"])

    user = users[int(input("选择用户:") or "1") - 1]

    password = input("教务密码（直接回车使用已保存的密码）:")

    if not password:

        password = decrypt_password(user["password"])

    print("================")
    print("入口:", entry)
    print("================")

    client = create_client(entry)

    # 1.登录
    ok = client.login(user["xh"], password)

    print("1.登录:", "PASS" if ok else "FAIL")

    if not ok:

        return

    # 2.cookie
    cookies = client.session.cookies.get_dict()

    print("2.cookie:", cookies)

    has_jsessionid = "JSESSIONID" in cookies

    print("2.JSESSIONID:", "PASS" if has_jsessionid else "FAIL")

    # 3.会话校验
    logged = client.check_login()

    print("3.check_login:", "PASS" if logged else "FAIL")

    # 4.成绩查询
    result = select_score(client.session, user["name"])

    if result is None:

        print("4.select_score: FAIL")

        return

    items = result.get("items", [])

    print("4.select_score: PASS，共", len(items), "门课")

    if items:

        print("   示例:", items[0].get("kcmc"), items[0].get("cj"))

    print("================")

    if has_jsessionid and logged and items:

        print("结论: 新入口可用，后续逻辑可复用")

    else:

        print("结论: 未完全通过，按上面 FAIL 项排查")


if __name__ == "__main__":

    main()
