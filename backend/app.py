from flask import Flask, request, send_from_directory, jsonify
import os
import asyncio
import threading
from mcp_client import main as generate_ppt

app = Flask(__name__)

# Directory where PPTs are saved (should match your ppt_server.py BASE_DIR)
PPT_DIR = r"C:\Users\gunta\Downloads\Calibo"

# Helper to run async code in a thread
loop = asyncio.new_event_loop()
def run_async(coro):
    return loop.run_until_complete(coro)

def generate_and_get_filename(topic, num_slides):
    import io, sys, re
    old_stdout = sys.stdout
    sys.stdout = mystdout = io.StringIO()
    try:
        run_async(generate_ppt(topic, num_slides))
    finally:
        sys.stdout = old_stdout
    output = mystdout.getvalue()
    # Look for the filename in the output
    match = re.search(r"PPT save result: (.+\.pptx)", output)
    if match:
        return match.group(1).strip()
    # Fallback: try to find the newest pptx file
    ppt_files = [f for f in os.listdir(PPT_DIR) if f.endswith('.pptx')]
    if ppt_files:
        return max(ppt_files, key=lambda f: os.path.getctime(os.path.join(PPT_DIR, f)))
    return None

@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json()
    topic = str(data.get('topic', '')).strip()
    try:
        num_slides = int(data.get('num_slides', 5))
    except Exception:
        num_slides = 5
    if not topic or not num_slides:
        return jsonify({'error': 'Missing topic or num_slides'}), 400
    result = {}
    def thread_target():
        result['filename'] = generate_and_get_filename(topic, num_slides)
    t = threading.Thread(target=thread_target)
    t.start()
    t.join()  # Wait for PPT generation to finish
    ppt_filename = result.get('filename')
    if ppt_filename:
        return jsonify({'filename': ppt_filename})
    else:
        return jsonify({'error': 'PPT generation failed'}), 500

@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(PPT_DIR, filename, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)
