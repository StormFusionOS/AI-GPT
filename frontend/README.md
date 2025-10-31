# Scraper Console

## Prerequisites
- Node.js 18+

## Getting Started
```bash
npm install
npm run dev
```
The development server boots on http://localhost:5173. Mock Service Worker starts automatically in development.

## Production Build
```bash
npm run build
npm run preview
```

## Testing
```bash
npm run test
```

## Linting & Formatting
```bash
npm run lint
npm run format
```

## Swapping to a Real Backend
Set `VITE_API_URL=https://crm.rivercityclean.com` (or another API endpoint) and disable MSW initialization in `src/main.tsx`.
