from fastapi.testclient import TestClient
from mock_colab import app

client = TestClient(app)

def test_chat_completions():
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "Qwen/Qwen2.5-7B-Instruct-GPTQ-Int4",
            "messages": [
                {"role": "user", "content": "Hello"}
            ]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "choices" in data
    assert len(data["choices"]) > 0
    assert data["choices"][0]["message"]["role"] == "assistant"
    assert "Mocked response based on query: Hello" in data["choices"][0]["message"]["content"]
    assert data["model"] == "Qwen/Qwen2.5-7B-Instruct-GPTQ-Int4"

def test_embed():
    response = client.post(
        "/embed",
        json={
            "texts": ["test text 1", "test text 2"]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "embeddings" in data
    assert len(data["embeddings"]) == 2
    for embedding in data["embeddings"]:
        assert len(embedding) == 384
        assert all(val == 0.1 for val in embedding)
