import requests
import rsa
import base64
from bs4 import BeautifulSoup


class JWXTLogin:

    def __init__(self):
        self.session = requests.Session()

        self.base_url = "http://59.74.174.150/jwglxt"

    def check_login(self):

        url = self.base_url + "/xtgl/index_initMenu.html?jsdm=xs"

        r = self.session.get(url)

        # 登录成功页面
        if "退出" in r.text:

            return True

        return False

    def get_csrf_token(self):

        url = self.base_url + "/xtgl/login_slogin.html"

        r = self.session.get(url)

        soup = BeautifulSoup(r.text, "html.parser")

        token = soup.find("input", {"name": "csrftoken"})["value"]

        return token

    def get_public_key(self):

        url = self.base_url + "/xtgl/login_getPublicKey.html"

        r = self.session.get(url)

        data = r.json()

        return (data["modulus"], data["exponent"])

    def rsa_encrypt(self, password, modulus, exponent):

        # Base64补齐
        modulus += "=" * (-len(modulus) % 4)
        exponent += "=" * (-len(exponent) % 4)

        n = int.from_bytes(base64.b64decode(modulus), "big")

        e = int.from_bytes(base64.b64decode(exponent), "big")

        pubkey = rsa.PublicKey(n, e)

        encrypted = rsa.encrypt(password.encode(), pubkey)

        return base64.b64encode(encrypted).decode()

    def login(self, username, password):

        # 1.获取csrf
        csrf = self.get_csrf_token()

        # 2.获取公钥
        modulus, exponent = self.get_public_key()

        # 3.RSA密码加密
        encrypted_pwd = self.rsa_encrypt(password, modulus, exponent)

        # 4.提交登录
        url = self.base_url + "/xtgl/login_slogin.html"

        data = [
            ("csrftoken", csrf),
            ("language", "zh_CN"),
            ("ydType", ""),
            ("yhm", username),
            ("mm", encrypted_pwd),
            ("mm", encrypted_pwd),
        ]

        response = self.session.post(url, data=data, allow_redirects=False)

        if response.status_code == 302:

            print("登录成功")

            print(self.session.cookies.get_dict())

            return True

        else:

            print("登录失败")
            print(response.text[:300])

            return False

