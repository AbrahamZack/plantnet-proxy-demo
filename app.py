from flask import Flask, request, jsonify
import requests
from io import BytesIO
import os
import mimetypes

app = Flask(__name__)

@app.route("/identify", methods=["POST"])
def identify():
    try:
        data = request.json
        image_url = data.get("image_url")
        organs = data.get("organs")
        api_key = data.get("api_key")

        if not api_key:
            return jsonify({"error": "Missing api_key"}), 400

        plantnet_api = f"https://my-api.plantnet.org/v2/identify/all?api-key={api_key}"

        img_resp = requests.get(image_url)
        if img_resp.status_code != 200:
            return jsonify({"error": "Failed to download image"}), 400
        img_data = BytesIO(img_resp.content)

        # 根据 URL 后缀判断文件类型
        ext = os.path.splitext(image_url)[-1].lower()
        mime_type = mimetypes.types_map.get(ext, 'image/jpeg')

        files = {
            'images': (f'plant{ext}', img_data, mime_type)
        }

        # 如果用户手动指定 organ，只尝试一次
        organ_list = [organs] if organs else ["leaf", "flower"]
        leaf_result = None
        leaf_score = -1
        flower_result = None
        flower_score = -1

        for organ_try in organ_list:
            payload = {'organs': organ_try}
            response = requests.post(plantnet_api, files=files, data=payload)

            if response.status_code == 200:
                result = response.json()
                if "results" in result and len(result["results"]) > 0:
                    best_score = result["results"][0].get("score", 0)
                    result["used_organ"] = organ_try

                    if organ_try == "leaf":
                        leaf_result = result
                        leaf_score = best_score
                        if best_score >= 0.7:
                            return jsonify(result)

                    elif organ_try == "flower":
                        flower_result = result
                        flower_score = best_score

        # 比较两个 organ 的识别结果
        if flower_score > leaf_score and flower_result:
            return jsonify(flower_result)
        elif leaf_result:
            return jsonify(leaf_result)

        return jsonify({"error": "Unable to identify plant from image"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
