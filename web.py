import json
from urllib.parse import urlparse
from flask import request, jsonify

from app_config import flask_app, redis_mayors


@flask_app.route('/cities/mayors-sp-sao-paulo.json')
def city():

    key = urlparse(request.url).path
    content = redis_mayors.get(key)

    if not content:
        return "", 404

    content = json.loads(content)
    last_update = redis_mayors.get("last_mayors_update")
    if last_update:
        content["last_update"] = last_update.decode("utf-8")

    return jsonify(content)


if __name__ == "__main__":
    flask_app.run()