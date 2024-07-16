import requests


def getTimeToCompelete(title, debug = False):
    gameName = title.split(' ')

    headers = {
        'authority': 'howlongtobeat.com',
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9,ja;q=0.8',
        'content-type': 'application/json',
        'dnt': '1',
        'origin': 'https://howlongtobeat.com',
        'referer': 'https://howlongtobeat.com/',
        'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"spotify"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Google Chrome :)',
    }

    json_data = {
        'searchType': 'games',
        'searchTerms': gameName,
        'searchPage': 1,
        'size': 20,
        'searchOptions': {
            'games': {
                'userId': 0,
                'platform': '',
                'sortCategory': 'popular',
                'rangeCategory': 'main',
                'rangeTime': {
                    'min': None,
                    'max': None,
                },
                'gameplay': {
                    'perspective': '',
                    'flow': '',
                    'genre': '',
                },
                'rangeYear': {
                    'min': '',
                    'max': '',
                },
                'modifier': '',
            },
            'users': {
                'sortCategory': 'postcount',
            },
            'lists': {
                'sortCategory': 'follows',
            },
            'filter': '',
            'sort': 0,
            'randomizer': 0,
        },
    }

    response = requests.post('https://howlongtobeat.com/api/search', headers=headers, json=json_data)
    
    try:
        compeltionTime = round(response.json()['data'][0]["comp_main"]/60/60,0)
        if (debug):
            print("Game Compeletion Time: " + str(compeltionTime))
        return compeltionTime
    except Exception:
        return 0