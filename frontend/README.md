# UnstressVN React SPA Frontend

React + TypeScript + Vite frontend cho dự án UnstressVN.

## Công nghệ sử dụng

- **React 19** - UI Library
- **TypeScript** - Type safety
- **Vite 7** - Build tool
- **TailwindCSS v4** - Styling
- **React Router v7** - Client-side routing
- **TanStack React Query** - Data fetching & caching
- **Axios** - HTTP client
- **i18next** - Internationalization (vi/en/de)

## Cài đặt

```bash
cd frontend
npm install
```

## Development

Chạy Vite dev server (hot reload):

```bash
npm run dev
```

Frontend sẽ chạy tại http://localhost:5173

**Lưu ý:** Cần chạy Django backend tại http://localhost:8000 để API hoạt động.

## Build Production

```bash
npm run build
```

Output sẽ được tạo trong thư mục `dist/`.

## Cấu trúc thư mục

```
frontend/
├── src/
│   ├── api/              # API client (axios)
│   ├── components/       # React components
│   │   └── ui/          # Reusable UI components
│   ├── contexts/         # React contexts (Auth, etc.)
│   ├── i18n/            # Internationalization
│   │   └── locales/     # Translation files
│   ├── layouts/         # Page layouts
│   ├── lib/             # Utility functions
│   ├── pages/           # Page components
│   ├── routes/          # Router configuration
│   ├── types/           # TypeScript types
│   ├── App.tsx          # Main App component
│   ├── index.css        # Global styles
│   └── main.tsx         # Entry point
├── dist/                 # Build output
├── package.json
├── tsconfig.json
└── vite.config.ts
```

## Tính năng

### Hoàn thành
- [x] Authentication (Login/Register/Logout)
- [x] User Profile (View/Edit)
- [x] Resources (List/Detail/Download)
- [x] Partner Search
- [x] Friend Requests
- [x] Chat (HTTP API)
- [x] Forum (Posts/Comments/Likes)
- [x] Search
- [x] i18n (Vietnamese/English/German)

## API Endpoints

Frontend sử dụng các API endpoints từ Django REST Framework:

- `/api/v1/auth/` - Authentication
- `/api/v1/resources/` - Resources
- `/api/v1/partners/` - Partner search
- `/api/v1/friend-requests/` - Friend requests
- `/api/v1/chat/` - Chat rooms & messages
- `/api/v1/forum/` - Forum posts & comments
- `/api/v1/search/` - Global search

## Kết nối với Django

### Development
- Vite dev server proxy các requests `/api` và `/media` đến Django (localhost:8000)
- WebSocket proxy `/ws` đến Django Channels

### Production
- Build frontend: `npm run build`
- Django serve SPA từ `/app/` route
- API endpoints tại `/api/v1/`

## Scripts

```bash
npm run dev       # Start dev server
npm run build     # Build for production
npm run preview   # Preview production build
npm run lint      # Run ESLint
```
