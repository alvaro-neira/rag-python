import requests
import os


def test_api_endpoints():
    port = os.getenv("PORT", "8000")
    base_url = f"http://localhost:{port}"

    print("Testing FastAPI endpoints...")

    # Test health endpoint
    print("\n1. Testing /health")
    response = requests.get(f"{base_url}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

    # Test query endpoint
    print("\n2. Testing /query")
    query_data = {
        "question": "What is a variable in Python?"
    }
    response = requests.post(f"{base_url}/query", json=query_data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Answer: {result['answer'][:200]}...")
        print(f"Sources: {len(result['sources'])} found")
    else:
        print(f"Error: {response.text}")


if __name__ == "__main__":
    print("Make sure your FastAPI server is running first!")
    print("Run: python -m app.main")
    print("Then run this test...")
    test_api_endpoints()
