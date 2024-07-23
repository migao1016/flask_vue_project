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
    group_counter = {}
    total_counter = Counter()  # 用于统计各个 rndnum 的总数

    for response in responses:
        content = response.get('content', '')
        soup = BeautifulSoup(content, 'html.parser')
        images = soup.find_all('img', {'class': 'emoticon'})

        group_match = re.search(r'速通：｛(\d+)[~-](\d+)｝', content)
        if group_match:
            start_num, end_num = group_match.groups()
            group_key = f"{start_num}~{end_num}"
            if group_key not in group_counter:
                group_counter[group_key] = Counter()

            for img in images:
                rndnum = img.get('rndnum')
                if rndnum:
                    group_counter[group_key][rndnum] += 1
                    total_counter[rndnum] += 1  # 更新各个 rndnum 的总数

    return group_counter, total_counter


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
    group_counter, total_counter = parse_responses(responses)

    color_map = {'1': '黑', '2': '紅', '3': '藍', '4': '綠'}
    result = {'groups': [], 'totals': []}

    # 按组统计
    for group, counts in group_counter.items():
        group_data = {'group': group, 'counts': []}
        for num in ['1', '2', '3', '4']:
            color = color_map.get(num, '未知')
            group_data['counts'].append({'color': color, 'count': counts[num]})
        result['groups'].append(group_data)

    # 计算总和
    for num in ['1', '2', '3', '4']:
        color = color_map.get(num, '未知')
        result['totals'].append({'color': color, 'count': total_counter[num]})

    return jsonify(result)


# if __name__ == '__main__':
#    app.run(host='0.0.0.0', port=5000, debug=True)
