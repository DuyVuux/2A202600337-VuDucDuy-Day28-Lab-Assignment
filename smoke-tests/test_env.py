import os
from pathlib import Path

def test_imports():
    import fastapi
    import uvicorn
    import httpx
    import prefect
    import kafka
    import pandas
    import pyarrow
    import redis
    import requests
    import qdrant_client
    import langsmith
    import pytest

    assert fastapi.__version__ is not None
    assert uvicorn.__version__ is not None
    assert httpx.__version__ is not None
    assert prefect.__version__ is not None
    assert pandas.__version__ is not None
    assert pyarrow.__version__ is not None
    assert redis.__version__ is not None
    assert requests.__version__ is not None

def test_env_file_exists():
    env_path = Path(__file__).parents[1] / ".env"
    assert env_path.exists()
    assert env_path.is_file()

def test_env_variables():
    from dotenv import load_dotenv
    env_path = Path(__file__).parents[1] / ".env"
    load_dotenv(dotenv_path=env_path)

    assert os.getenv("VLLM_NGROK_URL") == "http://localhost:8001"
    assert os.getenv("EMBED_NGROK_URL") == "http://localhost:8001"
    assert os.getenv("LANGCHAIN_API_KEY") == "dummy_key"
    assert os.getenv("LANGCHAIN_PROJECT") == "lab28-platform"
