import copy
import os
import time

from flask import Flask, make_response, jsonify, request
import pymongo
app = Flask('app')
mongoclient = pymongo.MongoClient(os.getenv("cstr"))
mongodb = mongoclient.NicoAutoDark
maincollection = mongodb.main
cache = {}
last_time = {}
def get_frame(vid):
    if cache.get(vid) and (time.time() - cache[vid]["time"]) < 300:
        ret = copy.deepcopy(cache[vid])
        if ret:
            return ret
        else:
            return None
    data = maincollection.find_one({"vid": vid})
    if data is None:
        cache[vid] = {"time": time.time()}
        return None
    data["time"] = time.time()
    cache[vid] = data
    return data

    

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', 'https://www.nicovideo.jp')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/')
def index():
    return jsonify({"message": "Welcome to NicoAutoDark!"})

@app.route('/<videoid>', methods=["get"])
def main(videoid):
    data = get_frame(videoid)
    if data is None:
        return make_response(jsonify({"message": f"Couldn't find timeline for {videoid}."}), 404)
    data.pop("_id", None)
    return make_response(jsonify(data), 200)

@app.route('/<videoid>', methods=["post"])
def upload(videoid):
    params = {"userid", "name", "frame", "pass"}
    if params - set(request.json.keys()):
        return make_response(jsonify({"message": "Some params are missing."}), 400)
    elif request.json["pass"] != os.getenv("pass"):
        return make_response(jsonify({"message": "You cannot access here."}), 403)
    uid = request.json["userid"]
    if last_time.get(uid) and (time.time() - last_time[uid]) < 300:
        return make_response(jsonify({"message": "You are being rate limited."}), 429)
    data = {
        "vid": videoid,
        "flip": request.json["frame"],
        "author": request.json["name"]
    }
    if maincollection.find_one({"vid": videoid}):
        maincollection.replace_one({"vid": videoid}, data)
    else:
        maincollection.insert_one(data)
    
    return make_response("", 204)



app.run(host='0.0.0.0', port=8080)