# recommender-service

FastAPI service that produces anime recommendations from an LLM (Groq) over context
retrieved from `vectorstore-service`, cached in Redis.

| Endpoint | Purpose |
|---|---|
| `POST /recommend` | `{query}` → `{query, recommendation, cached}` |
| `GET /health`, `GET /metrics` | liveness, Prometheus metrics |

**Flow:** hash the query → check Redis cache → on miss, call `vectorstore-service /search`,
build context, run an LCEL chain (`prompt | ChatGroq | StrOutputParser`), cache the answer
(`RECOMMENDATION_CACHE_TTL_SECONDS`), and return it. Requires `GROQ_API_KEY`.

Run: `npm run dev:recommender` (`:8003`).
