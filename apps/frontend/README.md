# Cubatron frontend (Vite + React + Tailwind)

Quick start (development):

1. Install Node >= 18
2. Install deps and run dev server:

```bash
cd apps/frontend
npm install
npm run dev
```

The dev server proxies `/api` to `http://127.0.0.1:8000` by default.

Build for production (CI recommended):

```bash
cd apps/frontend
npm run build
```

By default the build writes into `app/static` so the backend can serve the files
(production path: `/opt/cubatron/app/static`). In CI the repo workflow builds with Node 18
and can rsync the built files to the Raspberry Pi.
