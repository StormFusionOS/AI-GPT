# Client Portal

Client-facing portal for the AI SEO dashboard platform. The portal is optimised
for clients to review their service status, appointments, communications, and
billing history.

## Getting Started

```bash
cd client-portal
npm install
npm run dev
```

The development server boots at http://localhost:5174 and automatically starts
the Mock Service Worker to provide realistic API responses.

## Building & Testing

```bash
npm run build
npm run preview
npm run test
```

Set `VITE_API_URL` to your backend endpoint when wiring the portal to the real
API. Disable MSW by removing the `worker.start()` call inside `src/main.tsx`.
