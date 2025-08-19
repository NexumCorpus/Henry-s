# Henry's SmartStock AI - Frontend

React.js web dashboard for Henry's SmartStock AI inventory management system.

## Features

- **Authentication System**: JWT-based authentication with role-based access control
- **Responsive Layout**: Mobile-first design with collapsible sidebar navigation
- **Dark Mode**: Optimized for bar environments with automatic theme switching
- **Accessibility**: WCAG compliant with keyboard navigation and screen reader support
- **Error Handling**: Comprehensive error boundaries and loading states
- **State Management**: Redux Toolkit for predictable state management
- **TypeScript**: Full type safety throughout the application

## Tech Stack

- **React 18** with TypeScript
- **Vite** for fast development and building
- **Redux Toolkit** for state management
- **React Router** for client-side routing
- **Axios** for API communication
- **CSS Custom Properties** for theming
- **Vitest** for testing

## Getting Started

### Prerequisites

- Node.js 16+ and npm
- Backend API running on http://localhost:8000

### Installation

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.example .env

# Start development server
npm run dev
```

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm test` - Run tests
- `npm run test:watch` - Run tests in watch mode

## Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── auth/           # Authentication components
│   ├── common/         # Common UI components
│   └── layout/         # Layout components
├── hooks/              # Custom React hooks
├── pages/              # Page components
├── services/           # API services
├── store/              # Redux store and slices
├── types/              # TypeScript type definitions
├── App.tsx             # Main app component
└── main.tsx           # App entry point
```

## User Roles & Permissions

The application supports role-based access control:

- **Barback**: Inventory scanning, stock alerts
- **Bartender**: Real-time stock levels, pour tracking
- **Manager**: Analytics, automated ordering, forecasting
- **Admin**: Full system access, settings management

## Accessibility Features

- Keyboard navigation support
- Screen reader compatibility
- High contrast mode support
- Focus management
- ARIA labels and roles
- Skip links for main content

## Dark Mode

The application defaults to dark mode for optimal use in bar environments. Users can toggle between light and dark themes using the header button.

## Responsive Design

- Mobile-first approach
- Collapsible sidebar navigation
- Touch-friendly interface
- Optimized for tablets and phones

## Testing

The application includes comprehensive testing:

- Unit tests for components and utilities
- Integration tests for user flows
- Accessibility testing
- Visual regression testing

## Environment Variables

See `.env.example` for available configuration options:

- `VITE_API_BASE_URL` - Backend API URL
- `VITE_APP_NAME` - Application name
- `VITE_ENABLE_VOICE_COMMANDS` - Enable voice interface
- `VITE_ENABLE_COMPUTER_VISION` - Enable vision features

## Demo Credentials

For testing purposes, use these demo credentials:

- **Manager**: manager@henrys.com / password
- **Bartender**: bartender@henrys.com / password  
- **Barback**: barback@henrys.com / password

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Performance

- Code splitting for optimal loading
- Lazy loading of routes
- Optimized bundle size
- Service worker for caching (production)