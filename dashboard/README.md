# BotForge dashboard

React + TypeScript + Vite dashboard for local development. Enter the admin key manually. It is held in React memory only and cleared on reload or Disconnect.

For local Vite development, run `npm install` and `npm run dev` in this directory. Vite proxies `/api` to `http://127.0.0.1:8000`; start the backend separately. Run `npm run typecheck` and `npm run build` to verify the frontend.

Docker serves the production build through nginx, which proxies `/api` to the backend container. The dashboard is bound to `127.0.0.1:5173` on the host. This key entry flow is a local demo mechanism, not production authentication.
