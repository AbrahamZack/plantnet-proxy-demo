from flask import Flask, request, jsonify
import requests
from io import BytesIO

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

        files = {
            'images': ('plant.jpg', img_data, 'image/jpeg')
        }
        payload = {
            'organs': organs
        }

        response = requests.post(plantnet_api, files=files, data=payload)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
