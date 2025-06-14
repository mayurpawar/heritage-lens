# /opt/heritage-lens/app/services/vertexai.py

from vertexai.language_models import TextEmbeddingModel

def embed_query(query: str):
    # Use the same model as used for batch embedding
    model = TextEmbeddingModel.from_pretrained("text-embedding-005")  # <-- Replace if you used a different model
    embeddings = model.get_embeddings([query])
    # Extract the vector (should be a list of floats, len 768)
    if embeddings and hasattr(embeddings[0], "values"):
        return embeddings[0].values
    # Fallback for dict/list
    if isinstance(embeddings, list) and len(embeddings) == 1:
        return embeddings[0]
    raise RuntimeError("Failed to create embedding for query")
