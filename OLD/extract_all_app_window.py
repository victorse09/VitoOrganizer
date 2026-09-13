import json

with open('/home/vitokin/.gemini/antigravity/brain/d0f8c2fb-5694-4a6d-8453-e84c409b6071/.system_generated/logs/transcript.jsonl') as f:
    for i, line in enumerate(f):
        data = json.loads(line)
        if data.get('type') == 'TOOL_RESPONSE':
            output = str(data.get('output', ''))
            if 'app_window.py' in output and 'class MainWindow' in output:
                with open(f'old_app_window_{i}.txt', 'w') as out:
                    out.write(output)
print("Done extracting app_window chunks.")
