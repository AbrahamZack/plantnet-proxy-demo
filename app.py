from flask import Flask, request, jsonify
import requests
from io import BytesIO
import os
from mimetypes import guess_type
from urllib.parse import urlparse

app = Flask(__name__)

@app.route("/identify", methods=["POST"])
def identify():
    try:
        data = request.json
        image_url = data.get("image_url")
        organs = data.get("organs", "leaf")
        api_key = data.get("api_key")

        if not api_key:
            return jsonify({"error": "Missing api_key"}), 400

        plantnet_api = f"https://my-api.plantnet.org/v2/identify/all?api-key={api_key}"

        img_resp = requests.get(image_url)
        img_data = BytesIO(img_resp.content)

        parsed = urlparse(image_url)
        filename = os.path.basename(parsed.path)
        mimetype = guess_type(filename)[0] or 'application/octet-stream'

        files = {
            'images': (filename, img_data, mimetype)
        }
        
        payload = {
            'organs': [organs]  # 🔧 必须是列表形式
        }

        response = requests.post(plantnet_api, files=files, data=payload)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
