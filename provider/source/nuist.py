import datetime
import logging

import ddddocr as ocr
import requests
from playwright.sync_api import sync_playwright

from provider.source.base import SourceProvider, Course, WeeklyRecurrence

default_class_timetable = [
    8 * 60 * 60 + 00 * 60,
    8 * 60 * 60 + 55 * 60,
    10 * 60 * 60 + 10 * 60,
    11 * 60 * 60 + 5 * 60,
    13 * 60 * 60 + 45 * 60,
    14 * 60 * 60 + 40 * 60,
    15 * 60 * 60 + 55 * 60,
    16 * 60 * 60 + 50 * 60,
    18 * 60 * 60 + 45 * 60,
    19 * 60 * 60 + 40 * 60,
    20 * 60 * 60 + 35 * 60]  # in seconds


class NUISTSourceProvider(SourceProvider):
    def __init__(self, username: str, password: str, first_school_day: datetime.datetime, semester: str, headless=True,
                 class_timetable=default_class_timetable):
        self.__username = username
        self.__password = password
        self.__headless = headless
        self.__semester = semester
        self.__first_school_day = first_school_day
        self.__class_timetable = class_timetable
        self.__cookies = None
        super().__init__()

    def __get_cookies(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.__headless)
            page = browser.new_page()
            page.goto(
                "https://authserver.nuist.edu.cn/authserver/login?type=userNameLogin")
            page.wait_for_load_state('load')

            page.wait_for_selector('#username').fill(self.__username)
            page.wait_for_selector('#password').fill(self.__password)

            # Captcha
            captcha_image = page.wait_for_selector('#captchaImg').screenshot()
            model = ocr.DdddOcr(show_ad=False)
            captcha = model.classification(captcha_image)
            page.wait_for_selector('#captcha').fill(captcha)

            page.wait_for_selector('#login_submit').click()

            # Login course system
            page.goto(
                "http://jwxt.nuist.edu.cn/jwapp/sys/yjsrzfwapp/dbLogin/main.do")
            page.wait_for_load_state('load')
            page.wait_for_selector('#tyrzBtn').click()
            page.wait_for_url(
                'http://jwxt.nuist.edu.cn/jwapp/sys/emaphome/portal/index.do?forceCas=1')
            page.wait_for_load_state('load')
            page.goto(
                'http://jwxt.nuist.edu.cn/jwapp/sys/wdkb/*default/index.do?EMAP_LANG=zh#/xskcb')
            page.wait_for_load_state('load')

            # Get cookie
            cookies = page.context.cookies()
            self.__cookies = cookies
            browser.close()

        logging.info("Got sweet cookie, u want one?")
        return

    def __create_course(self, name: str, location: str, start_week: int, end_week: int, start_time: int, end_time: int,
                        weekday: int, duration_type: str) -> Course:
        start_date = self.__first_school_day + \
                     datetime.timedelta(days=(start_week - 1) * 7 + weekday)

        start_time = self.__class_timetable[start_time - 1]
        end_time = self.__class_timetable[end_time - 1]
        if start_time != end_time:
            end_time += 45 * 60

        start_date = start_date.replace(
            hour=start_time // 3600, minute=(start_time % 3600) // 60, second=start_time % 60)
        end_date = start_date.replace(
            hour=end_time // 3600, minute=(end_time % 3600) // 60, second=end_time % 60)

        recurrence = None
        if start_week != end_week:
            interval = 2 if duration_type == 'odd' else 1
            count = (end_week - start_week + 1) // interval
            recurrence = WeeklyRecurrence(interval, count)

        return Course(
            name=name,
            location=location,
            recurrence=recurrence,
            start_date=start_date,
            end_date=end_date,
        )

    def get_courses(self) -> set[Course]:
        if self.__cookies is None:
            self.__get_cookies()

        courses = set()

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-CN,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': 'http://jwxt.nuist.edu.cn',
            'DNT': '1',
            'Sec-GPC': '1',
            'Connection': 'keep-alive',
            'Referer': 'http://jwxt.nuist.edu.cn/jwapp/sys/wdkb/*default/index.do?EMAP_LANG=zh'
        }

        response = requests.post(
            'http://jwxt.nuist.edu.cn/jwapp/sys/wdkb/modules/xskcb/cxxszhxqkb.do',
            cookies={cookie['name']: cookie['value']
                     for cookie in self.__cookies},
            headers=headers,
            data=f'XNXQDM={self.__semester}'
            # data=f'XNXQDM=2024-2025-1'
        ).json()

        table = response['datas']['cxxszhxqkb']['rows']
        weekdays = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日']

        for c in table:
            name = c['KCM']
            location = c['JASMC']
            duration = c['ZCMC']  # 1-15周(单) / 1,2,3周
            weekday = c['SKXQ_DISPLAY']  # 星期x
            start_time = int(c['KSJC_DISPLAY'].replace(
                '第', '').replace('节', ''))
            end_time = int(c['JSJC_DISPLAY'].replace('第', '').replace('节', ''))

            # parse weekday to number
            weekday = weekdays.index(weekday)

            # parse duration to start and end week
            duration_type = 'normal'
            if '单' in duration:
                duration_type = 'odd'
                duration = duration.replace('(单)', '')
            elif '双' in duration:
                duration_type = 'even'
                duration = duration.replace('(双)', '')

            l = duration.split(',')
            for component in l:
                span = component.replace('周', '').split('-')
                start_week = int(span[0])
                end_week = int(span[1]) if len(span) > 1 else start_week

                course = self.__create_course(name, location, start_week, end_week, start_time, end_time, weekday,
                                              duration_type)
                courses.add(course)

        logging.info(f"Fetched {len(courses)} courses")
        return courses
