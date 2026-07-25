# 西科大教务助手

一个基于 Python 开发的西安科技大学教务系统成绩查询工具。

支持自动登录、Cookie缓存、成绩查询、成绩变化检测以及 Excel 导出。

---

## ✨ 功能特点

### 🔐 自动登录

- 支持教务系统账号密码登录
- 自动获取 CSRF Token
- 自动获取 RSA 公钥
- RSA 加密密码提交登录

### 🍪 Cookie缓存

支持登录状态缓存：

### 密码加密存储

用户密码不会明文保存。

使用 Fernet 对称加密：

用户文件中保存类似：

````json
{
    "name": "张三",
    "xh": "24403120101",
    "password": "gAAAAABxxxxx"
}


## ✨ 使用方法
Python版本推荐：
Python >= 3.10

安装依赖

执行：
```bash
pip install -r requirements.txt
````

第一次运行:
执行：

```bash
python main.py
```
