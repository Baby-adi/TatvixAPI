from sentence_transformers import SentenceTransformer
import torch

device = "cuda" if torch.cuda.is_available() else "cpu"
model_path = "/app/models/model"
model = SentenceTransformer(model_path).to(device=device)

def embedding_document_model(texts):
    embeddings = model.encode(texts,prompt_name="Retrieval-document",convert_to_tensor=False)
    return embeddings

def embedding_query_model(texts):
    embeddings = model.encode(texts,prompt_name="Retrieval-query",convert_to_tensor=False)
    return embeddings

