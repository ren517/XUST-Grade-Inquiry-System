# 西科大教务助手

一个基于 Python 开发的西安科技大学教务系统成绩查询工具。

支持自动登录、Cookie 缓存、成绩查询、成绩变化检测以及 Excel 导出。

支持两套登录入口：老教务系统 RSA 登录（默认）和统一用户中心 jwsso CAS 登录。

---

## ✨ 功能特点

### 🔐 自动登录

两套入口任选，登录之后的所有逻辑完全一致：

| 入口 | 取值 | 认证方式 |
|---|---|---|
| 老教务系统 | `legacy` | 取 `csrftoken` + RSA 公钥，`mm` 字段 RSA 加密提交 |
| 统一用户中心 | `jwsso` | 走教务 CAS 入口 → jwsso CAS 登录页取 `__token__` → AES 加密密码 → 带 ticket 回教务换会话 |
| 统一身份认证 | `ids` | ids CAS 备选通道（目前教务回调返回"应用未注册"，暂不可用） |

- 默认 `legacy`，行为与改造前完全一致
- 新入口只在"取 cookie"这一步不同，`score.py` / `history.py` 原样复用

### 🍪 Cookie 缓存

登录状态缓存在 `cookies/` 下，下次运行先校验，失效才重新登录。

两套入口的缓存**分开存放**，互不覆盖：

```
cookies/<学号>.json          # legacy
cookies/jwsso_<学号>.json    # jwsso
```

### 成绩查询与变化检测

- 查询全部课程成绩
- 与上次运行的历史记录对比，只打印新增/变化的课程
- 导出 `<姓名>_的成绩.xlsx`

### 密码加密存储

用户密码不会明文保存，使用 Fernet 对称加密：

```json
{
  "name": "张三",
  "xh": "24403990101",
  "password": "gAAAAABxxxxx"
}
```

---

## 🚀 使用方法

Python 版本推荐：>= 3.10

安装依赖：

```bash
pip install -r requirements.txt
```

### 老入口（默认）

```bash
python main.py
```

### 新入口（统一用户中心 jwsso）

```bash
python main.py --entry=jwsso
```

也可以在用户文件里固定，就不用每次带参数：

```json
{
  "name": "张三",
  "xh": "24403990101",
  "password": "gAAAAABxxxxx",
  "entry": "jwsso"
}
```

### 验证新入口是否可用

```bash
python verify_login.py --entry=jwsso
```

脚本会依次断言四项，全 PASS 说明新入口能拿到有效 cookie 且后续流程可复用：

```
1.登录: PASS
2.JSESSIONID: PASS
3.check_login: PASS
4.select_score: PASS，共 13 门课
```

首次运行 `main.py` 选 `0` 添加用户，之后按编号选择即可。

---

## 📁 目录结构

```
├── main.py              主流程：选用户 → 登录 → 查成绩 → 比历史 → 导出
├── login.py             老入口登录（JWXTLogin，RSA）
├── jwsso_login.py       新入口登录（JwssoLogin，jwsso CAS）
├── ids_login.py         备选入口（IdsLogin，ids CAS）
├── score.py             成绩查询 + Excel 导出
├── history.py           成绩历史对比
├── cookie_manager.py    用户与 Cookie 读写
├── crypto.py            密码 Fernet 加解密
├── verify_login.py      新入口验证脚本
├── explore_jwsso.py     jwsso 登录后页面探索（排查用）
├── users/               用户配置
├── cookies/             登录态缓存
├── history/             成绩历史快照
└── docs/新认证入口接入方案.md   新入口接入的完整分析与改造记录
```

三个登录类都继承自 `JWXTLogin`，只覆盖 `login()`，对外暴露同样的 `session` 和 `check_login()`，所以下游代码不需要判断走的是哪个入口。

---

## ⚠️ 注意事项

### jwsso 有登录失败次数限制

密码错误会提示"还可以尝试 N 次"，连续输错会锁定账号（约 30 分钟自动解锁）。**不要拿脚本反复试错密码。**

### 系统代理会导致教务 CAS 端点返回 503

走系统代理访问 `59.74.174.150` 的 CAS 端点会返回 503，直连正常。新入口已在 session 上设置 `trust_env = False` 强制直连；如果老入口遇到类似问题，可参照处理。

### AES 密钥不是固定值

jwsso 登录页的 AES key / iv 取自当前 `__token__` 的前 16 位，**每次请求都会变**，不能写死。（这是最初登录失败"账号不存在或密码错误"的根因——服务端解出的是乱码。）

### 新入口的链路

```
GET  http://59.74.174.150/jwglxt/auth/auth_casAuthLogin.html
  → 302 http://jwsso.xust.edu.cn/auth/cas/login?service=...
  → 取 __token__（同时作为 AES key）
  → POST 账号密码（AES-128-CBC / ZeroPadding / Base64）
  → 302 带 ticket
  → ticketlogin → index_initMenu → 拿到 JSESSIONID + route
```

### 老入口仍可用时无需切换

新入口是可选增强，不是替代。老入口正常的话直接 `python main.py` 即可。
