import json

app_window_content = None

with open('/home/vitokin/.gemini/antigravity/brain/d0f8c2fb-5694-4a6d-8453-e84c409b6071/.system_generated/logs/transcript.jsonl') as f:
    for line in f:
        data = json.loads(line)
        if data.get('type') == 'TOOL_RESPONSE' and data.get('name') == 'view_file':
            output = data.get('output', '')
            if 'class MainWindow' in output and 'class SmartCenterWidget' in output:
                app_window_content = output
                break

if app_window_content:
    with open('old_app_window.txt', 'w') as f:
        f.write(app_window_content)
    print("Extracted to old_app_window.txt")
else:
    print("Not found")
