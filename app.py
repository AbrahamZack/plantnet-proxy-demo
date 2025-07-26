from flask import Flask, request, jsonify, send_file
import requests
from io import BytesIO
import os
import mimetypes
import asyncio
import uuid
import edge_tts

app = Flask(__name__)
app.static_folder = "audios"

# ====================
# 植物识别接口
# ====================
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

        ext = os.path.splitext(image_url)[-1].lower()
        mime_type = mimetypes.types_map.get(ext, 'image/jpeg')

        files = {
            'images': (f'plant{ext}', img_data, mime_type)
        }

        organ_list = [organs] if organs else ["leaf", "flower"]
        leaf_result = flower_result = None
        leaf_score = flower_score = -1

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

        if flower_score > leaf_score and flower_result:
            return jsonify(flower_result)
        elif leaf_result:
            return jsonify(leaf_result)

        return jsonify({"error": "Unable to identify plant from image"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ====================
# 俄语语音合成接口
# ====================
AUDIO_DIR = "audios"
os.makedirs(AUDIO_DIR, exist_ok=True)

@app.route("/speak", methods=["GET"])
def speak():
    text = request.args.get("text", "").strip()
    if not text:
        return jsonify({"error": "Missing 'text' parameter"}), 400

    # 更安全的文件名（不暴露用户输入）
    filename = f"{uuid.uuid4().hex}.mp3"
    filepath = os.path.join(AUDIO_DIR, filename)

    voice = "ru-RU-SvetlanaNeural"
    try:
        asyncio.run(edge_tts.Communicate(text, voice).save(filepath))
    except Exception as e:
        return jsonify({"error": f"TTS failed: {str(e)}"}), 500

    file_url = f"https://{request.host}/audios/{filename}"
    return jsonify({
        "audio_url": file_url,
        "text": text
    })


# ====================
# 新增：音频播放支持（通过链接访问）
# ====================
@app.route("/audios/<filename>", methods=["GET"])
def get_audio(filename):
    filepath = os.path.join(AUDIO_DIR, filename)
    if not os.path.isfile(filepath):
        return jsonify({"error": "Audio file not found"}), 404
    return send_file(filepath, mimetype="audio/mpeg")


# ====================
# 启动入口
# ====================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
