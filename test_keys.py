import urllib.request, json

def test_key(key: str) -> None:
    url = 'https://openrouter.ai/api/v1/chat/completions'
    data = json.dumps({
        'model': 'openai/gpt-oss-120b:free',
        'messages': [{'role': 'user', 'content': 'ola'}],
        'max_tokens': 5
    }).encode('utf-8')
    headers = {
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json',
    }
    req = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            print(f'Key {key[:12]}... -> OK')
    except urllib.error.HTTPError as e:
        print(f'Key {key[:12]}... -> {e.code}')
    except Exception as e:
        print(f'Key {key[:12]}... -> Error: {e}')


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        test_key(sys.argv[1])
    else:
        print('Usage: python test_keys.py <api_key>')
