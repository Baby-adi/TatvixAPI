from flask import Flask,request,jsonify
from setupAPI.config import Config
from setupAPI.utils import Utils
import traceback
from mongoengine import connect
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

config = Config()
utils = Utils()

@app.route("/populate-mongodb",methods=["POST"]) #Test end point for dynamic testing, use Postman or thunder client or any API testing tool.
def test():
    files = request.files.getlist("file")
    if len(files) == 0:
        return jsonify({"error": "No files uploaded"}), 400
    
    results = []
    errors = []
    for file in files:
        try:
            data = file.read()
            filename = file.filename
            results.append(filename)
            utils.pdf_to_mongodb(data=data,filename=filename)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    response = {"message": "OCR processing completed", "processed_files": results}
    if errors:
        response["errors"] = errors

    return jsonify(response), 200


@app.route("/populate-weaviate",methods=["POST"])
def populate():
    try:
        client = config.weaviate_client
        data = utils.get_data()
        utils.store_data(data,client)
        return jsonify({"message": f"Successfully populated Weaviate with {len(data)} entries."}), 200
    except Exception as e:
        error_details = traceback.format_exc()
        print("Error details:", error_details)
        return jsonify({"error": str(e), "details": error_details}), 500


@app.route("/drop-weaviate-db", methods=["POST"])
def admin_login():
    try:
        client = config.weaviate_client
        client.collections.delete("Vectorbase")
    except Exception as e:
        print(f"Exception occured: {e}")
        return jsonify({"Error":e}),500
    return jsonify({"Message":"Deleted db"}),200


if __name__ == "__main__": #This is only for local development and in production, must use a lifcycle manager like @app.before_first_request() in flask.
    try:
        connect(host=os.getenv("MONGODB_URI")) #MongoDB connection before running wsgi server for flask.
        client = config.weaviate_client
        utils.create_weaviate_schema(client) #Create weavite db before running wsgi server for flask.
    except Exception as e:
        print(f"Exception occured leading server start-up failure -> {e}")

    app.run(host="0.0.0.0",port=5000,debug=True) #Run app.
