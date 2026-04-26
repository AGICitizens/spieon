# spieon-frontend

Next.js 15 (App Router, TypeScript).

```bash
npm install
npm run dev
```

API types are generated from the backend's OpenAPI schema:

```bash
# with backend running on :8000
npm run gen:api
```

This writes `lib/api-types.ts`, the only "shared code" between the two services.
