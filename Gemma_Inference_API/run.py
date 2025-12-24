from flask import Flask,jsonify,request
from service import embedding_document_model,embedding_query_model

app = Flask(__name__)


@app.route("/v1/.well-known/ready", methods=["GET"]) #For Health checks of flask app.
@app.route("/.well-known/ready", methods=["GET"])
def ready():
    return jsonify({"status": "ready"}), 200

@app.route("/v1/meta", methods=["GET"])
def meta():
    return {
        "name": "legal embedding searcher",
        "version": "1.0.0",
        "description": "Enhanced by gemma-embedding 300m for semantic legal search.",
        "framework": "transformers",
        "transformers": {
            "model": "gemma-300m",
            "framework": "pytorch"
        }
    }, 200


@app.route("/vectors",methods=["POST"])
def embed():
    try:
        body = request.get_json(force=True) #getting weaviates post data from population batch.
        embed_type = request.args.get('embed_type')
        print("Received /vectors payload:", body)
        texts = body.get("text",[]) #Extracting text according to weaviates request.
        if not texts or not isinstance(texts,list):
            return jsonify({"error": "Invalid or missing 'text' key"}), 400
        if embed_type == "document":
            embeddings = embedding_document_model(texts=texts)
        
        elif embed_type == "query":
            embeddings = embedding_query_model(texts=texts)

        return jsonify({
            "vectors":[emb.tolist() for emb in embeddings]
        }),200

    except Exception as e:
        return jsonify({"error":str(e)}),500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081)