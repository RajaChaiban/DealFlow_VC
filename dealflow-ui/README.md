# DealFlow AI Copilot - Frontend

A modern Next.js 14 application for private equity deal analysis powered by AI.

## Features

- **Dashboard**: Overview of all deals with key metrics and quick actions
- **Deal Analysis**: Upload pitch decks and get AI-powered analysis with step-by-step progress tracking
- **Deal Comparison**: Side-by-side comparison of multiple deals with winner rankings
- **Pipeline Management**: Kanban-style board for managing deals through investment stages
- **AI Chat**: Conversational interface for asking questions about deals

## Tech Stack

- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- Lucide React (Icons)
- Backend API: http://localhost:8000

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- Backend API running at http://localhost:8000

### Installation

1. Install dependencies:

```bash
npm install
```

2. Run the development server:

```bash
npm run dev
```

3. Open [http://localhost:3000](http://localhost:3000) in your browser

## Project Structure

```
dealflow-ui/
├── src/
│   ├── app/
│   │   ├── layout.tsx          # Root layout with sidebar
│   │   ├── page.tsx            # Dashboard home page
│   │   ├── deals/
│   │   │   └── page.tsx        # Deal analysis page
│   │   ├── compare/
│   │   │   └── page.tsx        # Deal comparison page
│   │   ├── pipeline/
│   │   │   └── page.tsx        # Pipeline kanban board
│   │   └── chat/
│   │       └── page.tsx        # Chat interface
│   ├── components/
│   │   └── Sidebar.tsx         # Navigation sidebar
│   ├── lib/
│   │   └── utils.ts            # Utility functions
│   ├── types/
│   │   └── index.ts            # TypeScript type definitions
│   └── globals.css             # Global styles and theme
├── public/                     # Static assets
├── package.json
├── tsconfig.json
├── tailwind.config.ts
└── next.config.js
```

## Design System

### Color Palette

- **Background**: Deep navy (`#0f1419`)
- **Primary**: Blue (`#3b82f6`)
- **Secondary**: Slate gray
- **Accent**: Muted gold
- **Success**: Green
- **Warning**: Amber
- **Danger**: Red

### Key Components

- **Glass Effect Cards**: `glass-effect` class with backdrop blur
- **Stat Cards**: Color-coded metrics with icons
- **Badge System**: Success, warning, danger, and info badges
- **Progress Indicators**: Step-by-step analysis tracking
- **Drag & Drop**: File upload zones with visual feedback

## API Integration

The application connects to the backend at `http://localhost:8000` with the following endpoints:

- `GET /api/deals` - Fetch all deals
- `POST /api/analyze` - Analyze a pitch deck
- `POST /api/compare` - Compare multiple deals
- `GET /api/chat/sessions` - Get chat sessions
- `POST /api/chat` - Send chat message
- `PATCH /api/deals/:id` - Update deal stage

## Features by Page

### Dashboard (`/`)
- Total deals analyzed stats
- Recent analyses list
- Pipeline overview mini chart
- Quick action buttons

### Deal Analysis (`/deals`)
- Drag-and-drop file upload
- Company name input
- 5-step progress indicator
- Tabbed results (Summary, Financials, Risks, Valuation)
- Export functionality

### Deal Comparison (`/compare`)
- Upload 2-3 deals
- Winner banner with trophy
- Side-by-side comparison table
- Strengths and weaknesses breakdown

### Pipeline (`/pipeline`)
- 7 stage columns (New → Closed Won/Passed)
- Drag-and-drop cards between stages
- Priority badges
- Column counts and stats

### Chat (`/chat`)
- Session management sidebar
- AI-powered responses
- Deal context selector
- Suggested questions
- Message history

## Customization

### Theme Colors

Edit `src/app/globals.css` to customize the color scheme:

```css
:root {
  --primary: 217 91% 60%;
  --background: 222 47% 11%;
  /* ... other colors */
}
```

### API URL

Edit `src/lib/utils.ts` to change the backend URL:

```typescript
export const API_BASE_URL = "http://localhost:8000";
```

## Build for Production

```bash
npm run build
npm start
```

## License

Private - DealFlow AI Copilot
