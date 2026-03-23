# Project Structure

```
frontend/
├── app/                # main application code (Expo router)
│   ├── (tabs)/            # tab-based navigation screens
│   ├── (auth)/            # authentication screens
│   └── _layout.tsx        # root layout
├── assets/             # static assets (images, icons, fonts, etc)
├── components/         # reusable UI components
│   ├── common/            # generic components (button, input, etc)
│   └── features/          # feature-specific components
├── constants/          # app-wide constants
├── hooks/              # custom react hooks
├── types/              # type definitions (models, api types, etc)
├── utils/              # helper functions and utilities
└── __tests__/          # test files (unit, integration testing)
```

# Development

## Setup & Installation

### Requirements

- Node version: v22.21.1

### VS Code Setup

- For proper formatting to work while you're coding:
  - Install Prettier (esbenp.prettier-vscode) VS Code Extension
  - If formatting still doesn't work, try opening VS Code window at `frontend` folder, not the root of the `capstone` repository

### Run the Application (Expo)

This is an [Expo](https://expo.dev) project created with [`create-expo-app`](https://www.npmjs.com/package/create-expo-app).

1. Install frontend node dependencies

```bash
cd frontend
npm install
```

2. Start the frontend app

```bash
npx expo start
```

### Build the Application (for Android)

1. Install EAS CLI (if not already installed)

```bash
npm install -g eas-cli
```

2. Login to your Expo account

```bash
eas login
```

3. Build the app for Android

```bash
eas build --profile development --platform android
```

### Launch App in Android Emulator

1. Open Android Emulator → More Actions → Virtual Device Manager → Start your device.

2. Run the app on Expo (follow [these steps](#run-the-application-expo))

- If app screen on emulator shows error on launch instead of bundling the app, might have to manually type in `<ip address>:8081` for the local server on the expo app
