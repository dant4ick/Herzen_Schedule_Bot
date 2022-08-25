import requests as request

if __name__ == '__main__':
    schedule = request.get(r'https://guide.herzen.spb.ru/static/schedule.php')
