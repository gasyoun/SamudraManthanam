import httpx
import json

def test():
    query = "Арджун"
    print(f"Testing search for: {query}")
    r = httpx.post('http://localhost:8000/api/search', json={'query': query, 'mode': 'plain'})
    data = r.json()
    print(f"Query: {data.get('query')}")
    print(f"Total: {data.get('total')}")
    print(f"Sources Hit: {data.get('sources_hit')}")
    print(f"Elapsed: {data.get('elapsed_ms')} ms")

if __name__ == "__main__":
    test()
