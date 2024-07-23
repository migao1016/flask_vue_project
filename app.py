from flask import Flask, render_template, request, jsonify
import requests
import re
from bs4 import BeautifulSoup
from collections import Counter

app = Flask(__name__)

def fetch_images(api_url, payload):
    response = requests.post(api_url, json=payload)
    if response.status_code != 200:
        return []
    data = response.json()
    responses = data.get('responses', [])
    return responses

def parse_responses(responses):
    total_counter = Counter()  # 用于统计各个 rndnum 的总数

    for response in responses:
        content = response.get('content', '')
        soup = BeautifulSoup(content, 'html.parser')
        images = soup.find_all('img', {'class': 'emoticon', 'alt': '(bzzz)'})

        for img in images:
            rndnum = img.get('rndnum')
            if rndnum:
                total_counter[rndnum] += 1  # 更新各个 rndnum 的总数

    return total_counter

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/fetch', methods=['POST'])
def fetch():
    url = request.json.get('url')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    response = requests.get(url)
    if response.status_code != 200:
        return jsonify({'error': 'Failed to fetch the URL'}), 400

    plurk_id = re.search(r'data-pid="(\d+)"', response.text)
    if not plurk_id:
        return jsonify({'error': 'Failed to find plurk_id'}), 400

    plurk_id = plurk_id.group(1)
    api_url = "https://www.plurk.com/Responses/get"
    payload = {"plurk_id": plurk_id, "from_response_id": 0}

    responses = fetch_images(api_url, payload)
    total_counter = parse_responses(responses)

    color_map = {'1': '黑', '2': '紅', '3': '藍', '4': '綠'}
    result = {'totals': []}

    # 计算总和
    for num in ['1', '2', '3', '4']:
        color = color_map.get(num, '未知')
        result['totals'].append({'color': color, 'count': total_counter[num]})

    return jsonify(result)

# if __name__ == '__main__':
#    app.run(host='0.0.0.0', port=5000, debug=True)
