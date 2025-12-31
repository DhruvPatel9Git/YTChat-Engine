import time
from typing import Any, Dict, List, Optional

def handle_score(message: Dict[str, Any]) -> Dict[str, Any]:
    """Simple placeholder scoring function.

    Returns a dict with a numeric `score` and any tags.
    """
    text = message.get("text", "")
    score = 0.0
    if len(text) > 100:
        score += 0.5
    if "!" in text:
        score += 0.2
    return {"score": score, "tags": []}


def handle_chain(message: Dict[str, Any], history: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    """Append message to an in-memory chain/history and return updated history."""
    if history is None:
        history = []
    entry = {
        "id": message.get("id"),
        "author": message.get("author", {}),
        "text": message.get("text"),
        "time": message.get("time"),
    }
    history.append(entry)
    # Keep last 100 messages
    return history[-100:]


def handle_chroma(message: Dict[str, Any], chroma_client: Optional[Any] = None) -> None:
    """Store a message into Chroma vector DB if available. This is a best-effort placeholder.

    Attempts to import `chromadb` and create/append to a collection named 'yt_chat'.
    """
    try:
        import chromadb
        from chromadb.config import Settings
    except Exception:
        return

    # Try to create a local client if none supplied
    try:
        client = chroma_client or chromadb.Client()
        collection_name = "yt_chat"
        try:
            collection = client.get_collection(collection_name)
        except Exception:
            collection = client.create_collection(collection_name)

        # Use message id as document id
        doc_id = message.get("id") or str(time.time())
        text = message.get("text", "")
        metadata = {"author": message.get("author", {}), "time": message.get("time")}
        collection.add(ids=[doc_id], documents=[text], metadatas=[metadata])
    except Exception:
        return
