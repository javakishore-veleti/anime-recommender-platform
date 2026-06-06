# customer-portal (AniMatch)

Angular 21 customer-facing portal. Users describe a vibe and get three AI-curated anime
recommendations. Talks to `recommender-service` (`:8003`) over HTTP.

- **Routes:** `/` (search + results), `/about`
- **Design:** Indigo & Teal design system (`src/styles.scss`), gradient hero, soft-shadow cards.
- **State:** Angular signals; lazy-loaded standalone pages.

```bash
npm install
npm start          # ng serve on http://localhost:4200
npm run build      # production build → dist/
```

API base URLs are in `src/environments/`. Requires the Middleware services running
(`npm run localhost:services:start-all` from the repo root) and a `GROQ_API_KEY` configured for the recommender.
