import logging
from pathlib import Path

import requests as request
from bs4 import BeautifulSoup
from bs4.element import NavigableString
import json

from config import BASE_DIR

SCHEDULE_DATE_URL = r'https://guide.herzen.spb.ru/static/schedule_dates.php?id_group='


def parse_groups():
    groups = {}

    schedule = request.get(r'https://guide.herzen.spb.ru/static/schedule.php')
    soup = BeautifulSoup(schedule.text, 'html.parser')

    for faculty in soup.find('h1').find_next_siblings('h3'):
        groups[faculty.text] = {}
        forms = {}
        for education_form in faculty.find_next_sibling('div').find_all('h4'):
            forms[education_form.text] = {}
            form = forms[education_form.text]

            for data in education_form.find_next_sibling('ul').find_all('li'):
                id_div = data.div
                group_id = data.find('div').find('button')['onclick']
                group_id = group_id.split("'")[1].split('=')[1].split('&')[0]
                id_div.decompose()
                stage, course, group = data.text.strip().split(', ')

                if stage not in form.keys():
                    form[stage] = {}
                    form[stage][course] = {}
                    form[stage][course][group] = group_id
                elif course not in form[stage].keys():
                    form[stage][course] = {}
                    form[stage][course][group] = group_id
                else:
                    form[stage][course][group] = group_id
            groups[faculty.text].update(forms)

    with open(Path(BASE_DIR / 'groups.json'), 'w', encoding='UTF-8') as output:
        json.dump(groups, output, indent=2, ensure_ascii=False)


async def parse_date_schedule(group, sub_group=None, date_1=None, date_2=None):
    if date_1 and not date_2:
        date_2 = date_1

    url = f"{SCHEDULE_DATE_URL}{group}&date1={date_1}&date2={date_2}"
    schedule_response = request.get(url)

    logging.info(f"group: {group}, sub_group: {sub_group}, date: {date_1} - {date_2}, "
                 f"url: {url}, r_code: {schedule_response.status_code}")

    soup = BeautifulSoup(schedule_response.content, features="html.parser")

    if soup.find('a', string='другую группу'):  # No classes at that period
        return {}

    if soup.find('tbody'):
        courses_column = soup.find('tbody').findAll('tr')
    else:
        return

    schedule_courses = {}
    day_name = ''
    for class_number in range(len(courses_column)):

        class_time = courses_column[class_number].find('th').text

        if courses_column[class_number].find('th', {'class': 'dayname'}):
            day_name = courses_column[class_number].find('th', {'class': 'dayname'}).text
            continue

        course = courses_column[class_number].findAll('td')

        if (len(course) > 1) and sub_group != 0:  # If multiple classes at the same time
            course = course[sub_group - 1]
        else:
            course = course[0]

        if not course.find('strong'):  # If class not found
            continue

        class_names = course.findAll('strong')
        for class_name in class_names:
            class_type = class_name.next.next
            if type(class_name.next) is not NavigableString:
                class_type = class_type.next

            class_mod = class_type.next.next
            if type(class_mod) is not NavigableString:
                class_mod = ''
            else:
                class_mod = class_mod.text.strip()

            class_teacher = ''
            class_room = ''

            if "дистанционное обучение" not in course.text:
                class_teacher = class_type.next.next.next
                class_room = class_teacher.next.next

                class_teacher = class_teacher.text
                class_room = str(class_room.text).strip(", \n")

            if day_name not in schedule_courses.keys():
                schedule_courses[day_name] = []
            schedule_courses[day_name].append({
                'time': class_time,
                'mod': class_mod,
                'name': class_name.text,
                'type': class_type.strip(),
                'teacher': class_teacher,
                'room': class_room
            })
    if not schedule_courses:
        return {}
    return schedule_courses, url
