import json
from pprint import pprint

import requests as request
from bs4 import BeautifulSoup


def parse_groups():
    groups = {}

    schedule = request.get(r'https://guide.herzen.spb.ru/static/schedule.php')
    soup = BeautifulSoup(schedule.text, 'html.parser')
    for faculty in soup.find('h1').find_next_siblings('h3'):
        groups[faculty.text] = {}
        forms = {}
        for education_form in faculty.find_next_sibling('div').find_all('h4'):
            forms[education_form.text] = {}

            for data in education_form.find_next_sibling('ul').find_all('li'):
                id_div = data.div
                group_id = data.find('div').find('button')['onclick']
                group_id = group_id.split("'")[1]
                id_div.decompose()
                stage, course, group = data.text.strip().split(', ')

                if stage not in forms[education_form.text].keys():
                    forms[education_form.text][stage] = {}
                    forms[education_form.text][stage][course] = {}
                    forms[education_form.text][stage][course][group] = group_id
                elif course not in forms[education_form.text][stage].keys():
                    forms[education_form.text][stage][course] = {}
                    forms[education_form.text][stage][course][group] = group_id
                else:
                    forms[education_form.text][stage][course][group] = group_id
            groups[faculty.text].update(forms)

    with open('groups.json', 'w', encoding='UTF-8') as output:
        json.dump(groups, output, indent=2, ensure_ascii=False)


if __name__ == '__main__':
    parse_groups()
