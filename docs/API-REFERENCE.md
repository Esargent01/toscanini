# API Reference

Toscanini exposes a FastAPI server for RAG retrieval.

## Base URL

```
http://localhost:8000
```

## Endpoints

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "retriever_loaded": true
}
```

---

### POST /retrieve

Generic retrieval endpoint for querying the vector store.

**Request:**
```json
{
  "query": "How do I implement authentication in Next.js?",
  "source_types": ["nextjs", "owasp"],  // optional
  "top_k": 5  // optional, default: 5
}
```

**Response:**
```json
{
  "chunks": [
    {
      "id": 169,
      "content": "## Use of authentication protocols...",
      "source_url": "https://cheatsheetseries.owasp.org/...",
      "source_type": "owasp",
      "section": "authentication",
      "title": "Authentication Cheat Sheet",
      "version": "",
      "similarity": 0.72
    }
  ]
}
```

---

### POST /retrieve-for-context

Context-aware retrieval optimized for Kleiber integration. Automatically queries multiple categories based on detected keywords.

**Request:**
```json
{
  "user_input": "I want to build a SaaS app with user authentication and Stripe payments"
}
```

**Response:**
```json
{
  "formatted_context": "## Reference Documentation\n\nThe following is current, authoritative documentation...\n\n## Next.js App Router Patterns\n\n### Middleware\n...\n\n## Security Requirements (OWASP)\n\n### Authentication Cheat Sheet\n...",
  "raw": {
    "nextjs": [
      {
        "id": 51,
        "content": "### Setting Headers...",
        "source_url": "https://nextjs.org/docs/...",
        "source_type": "nextjs",
        "section": "routing",
        "title": "Middleware",
        "similarity": 0.55
      }
    ],
    "security": [
      {
        "id": 169,
        "content": "## Use of authentication protocols...",
        "source_url": "https://cheatsheetseries.owasp.org/...",
        "source_type": "owasp",
        "section": "authentication",
        "title": "Authentication Cheat Sheet",
        "similarity": 0.54
      }
    ],
    "seo": []
  }
}
```

**Query Logic:**

| Keyword Detection | Sources Queried |
|-------------------|-----------------|
| Always | `nextjs` (3 chunks) |
| auth, login, user, password, payment, stripe, data | `owasp` (3 chunks) |
| landing, marketing, blog, portfolio, business, seo | `seo` (2 chunks) |

---

## Error Responses

### 503 Service Unavailable

Retriever not initialized (model still loading).

```json
{
  "detail": "Retriever not initialized"
}
```

### 500 Internal Server Error

```json
{
  "detail": "Error message describing the issue"
}
```

---

## Integration Example

### TypeScript/JavaScript

```typescript
const RAG_API_URL = "http://localhost:8000";

async function retrieveContext(userInput: string) {
  const response = await fetch(`${RAG_API_URL}/retrieve-for-context`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_input: userInput }),
  });

  if (!response.ok) {
    console.error("RAG retrieval failed");
    return null;
  }

  return response.json();
}

// Usage
const context = await retrieveContext("SaaS with user auth");
if (context?.formatted_context) {
  // Inject into your LLM prompt
  const augmentedPrompt = `${basePrompt}\n\n${context.formatted_context}`;
}
```

### Python

```python
import requests

RAG_API_URL = "http://localhost:8000"

def retrieve_context(user_input: str) -> dict | None:
    try:
        response = requests.post(
            f"{RAG_API_URL}/retrieve-for-context",
            json={"user_input": user_input}
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"RAG retrieval failed: {e}")
        return None

# Usage
context = retrieve_context("SaaS with user auth")
if context and context.get("formatted_context"):
    augmented_prompt = f"{base_prompt}\n\n{context['formatted_context']}"
```

### cURL

```bash
curl -X POST http://localhost:8000/retrieve-for-context \
  -H "Content-Type: application/json" \
  -d '{"user_input": "SaaS app with authentication"}'
```
