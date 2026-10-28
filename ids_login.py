import base64
import os
import random
import re

from bs4 import BeautifulSoup
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from login import JWXTLogin


# =====================
# 统一身份认证（新入口）
# =====================

IDS_BASE = "https://ids.xust.edu.cn/authserver"

# 老教务系统接收 CAS ticket 的回调地址（service）
# 若实测回调不生效，可改为：
# http://59.74.174.150/jwglxt/xtgl/index_initMenu.html?jsdm=xs
DEFAULT_SERVICE = "http://59.74.174.150/jwglxt/xtgl/login_slogin.html"

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36"

# 与前端 encrypt.js 保持一致的随机串字符集
AES_CHARS = "ABCDEFGHJKMNPQRSTWXYZabcdefhijkmnprstwxyz2345678"


class IdsLogin(JWXTLogin):
    """
    新认证入口：统一身份认证平台（CAS）

    复用 JWXTLogin 的 session / base_url / check_login，
    只替换 login() 的取 cookie 方式。

    最终目标与老入口一致：
    让 session 持有 59.74.174.150 域下的 JSESSIONID + route，
    之后 select_score() 等原有逻辑可直接复用。
    """

    def __init__(self, service=None):

        super().__init__()

        self.service = service or os.environ.get("IDS_SERVICE") or DEFAULT_SERVICE

    # =====================
    # 密码加密
    # =====================

    def random_string(self, n):

        return "".join(random.choice(AES_CHARS) for _ in range(n))

    def aes_encrypt(self, password, salt):
        """
        与页面 encrypt.js 的 encryptPassword 等价：
        AES-128-CBC + PKCS7，key = pwdEncryptSalt，iv = 随机16位
        明文 = 随机64位 + 明文密码
        """

        key = salt.encode("utf-8")

        iv = self.random_string(16).encode("utf-8")

        data = (self.random_string(64) + password).encode("utf-8")

        padder = padding.PKCS7(128).padder()

        data = padder.update(data) + padder.finalize()

        cipher = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()

        return base64.b64encode(cipher.update(data) + cipher.finalize()).decode()

    # =====================
    # 登录页解析
    # =====================

    def get_login_page(self):

        url = IDS_BASE + "/login"

        r = self.session.get(
            url,
            params={"service": self.service},
            headers={"User-Agent": UA},
        )

        return r.text

    def parse_login_page(self, html):
        """
        取出表单隐藏域与加密盐
        """

        soup = BeautifulSoup(html, "html.parser")

        form = soup.find("form", {"id": "loginFromId"})

        fields = {}

        if form is not None:

            for i in form.find_all("input"):

                name = i.get("name")

                if name:

                    fields[name] = i.get("value", "")

        salt_tag = soup.find("input", {"id": "pwdEncryptSalt"})

        salt = salt_tag["value"] if salt_tag else ""

        return fields, salt

    # =====================
    # 验证码（可选）
    # =====================

    def need_captcha(self, username):

        url = IDS_BASE + "/checkNeedCaptcha.htl"

        try:

            r = self.session.get(url, params={"username": username})

            return bool(r.json().get("isNeed"))

        except Exception:

            return False

    def get_captcha_image(self):

        url = IDS_BASE + "/getCaptcha.htl"

        r = self.session.get(url, params={"_": int(random.random() * 1e10)})

        return r.content

    # =====================
    # 登录
    # =====================

    def login(self, username, password, captcha="", on_captcha=None):

        # 1.打开带 service 的登录页
        html = self.get_login_page()

        if "应用未注册" in html:

            print("CAS 未注册该回调地址:", self.service)

            print("请用浏览器抓包确认 service，并通过 IDS_SERVICE 或 --service 指定")

            return False

        fields, salt = self.parse_login_page(html)

        if not fields.get("execution") or not salt:

            print("登录页解析失败，未取到 execution / pwdEncryptSalt")

            return False

        # 2.判断验证码
        if self.need_captcha(username):

            if on_captcha is None:

                print("需要验证码，未提供验证码输入回调")

                return False

            captcha = on_captcha(self.get_captcha_image())

        # 3.AES加密密码
        encrypted_pwd = self.aes_encrypt(password, salt)

        # 4.提交登录
        url = IDS_BASE + "/login"

        data = {
            "username": username,
            "password": encrypted_pwd,
            "captcha": captcha,
            "lt": fields.get("lt", ""),
            "dllt": fields.get("dllt", "generalLogin"),
            "execution": fields["execution"],
            "_eventId": fields.get("_eventId", "submit"),
            "rmShown": "1",
        }

        headers = {
            "User-Agent": UA,
            "Referer": IDS_BASE + "/login",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        r = self.session.post(
            url,
            params={"service": self.service},
            data=data,
            headers=headers,
            allow_redirects=False,
        )

        # 5.判断是否下发 ticket
        location = r.headers.get("Location", "")

        if "ticket=" not in location:

            reason = self.parse_error(r.text)

            print("登录失败:", reason)

            return False

        # 6.携带 ticket 回到老教务系统换取会话
        self.session.get(location, headers={"User-Agent": UA})

        return True

    def parse_error(self, html):

        soup = BeautifulSoup(html, "html.parser")

        for i in ("msg", "errorMsg", "errormsg"):

            tag = soup.find(id=i)

            if tag and tag.get_text(strip=True):

                return tag.get_text(strip=True)

        m = re.search(r'id="msg"[^>]*>(.*?)<', html, re.S)

        if m:

            return m.group(1).strip()

        return "未知错误（可能是账号密码错误或需要验证码）"
