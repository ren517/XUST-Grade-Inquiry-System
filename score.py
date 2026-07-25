import requests
import time
import pandas as pd


def select_score(session, name):

    BASE_URL = "http://59.74.174.150/jwglxt/"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36",
        "Referer": BASE_URL,
    }

    url = BASE_URL + "cjcx/cjcx_cxXsgrcj.html?" "doType=query&gnmkdm=N305005"

    data = {
        "xnm": "2025",  # 2025-2026学年
        "xqm": "12",  # 2025-2026学年第2学期
        "_search": "false",
        "nd": int(time.time() * 1000),
        "queryModel.showCount": "100",
        "queryModel.currentPage": "1",
        "queryModel.sortName": "",
        "queryModel.sortOrder": "asc",
        "time": "0",
    }

    response = session.post(url, headers=headers, data=data)

    print("状态码:", response.status_code)

    try:

        result = response.json()

    except Exception:

        print("返回不是JSON:")
        print(response.text[:500])

        return None

    courses = result["items"]

    df = pd.DataFrame(courses)

    score = df[["xnmmc", "xqmmc", "kcmc", "kcxzmc", "xf", "cj", "xfjd"]]

    score = score.rename(
        columns={
            "xnmmc": "学年",
            "xqmmc": "学期",
            "kcmc": "课程名称",
            "kcxzmc": "课程性质",
            "xf": "学分",
            "cj": "成绩",
            "xfjd": "学分绩点",
        }
    )

    print(score)

    score.to_excel(f"{name}_的成绩.xlsx", index=False)

    return result
