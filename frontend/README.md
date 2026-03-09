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

- In the output, you'll find options to open the app in a
  - [development build](https://docs.expo.dev/develop/development-builds/introduction/)
  - [Android emulator](https://docs.expo.dev/workflow/android-studio-emulator/)
  - [iOS simulator](https://docs.expo.dev/workflow/ios-simulator/)
  - [Expo Go](https://expo.dev/go), a limited sandbox for trying out app development with Expo

You can start developing by editing the files inside the **app** directory. This project uses [file-based routing](https://docs.expo.dev/router/introduction).

### Build the Application

#### Build for Android

1. Install EAS CLI (if not already installed)

```bash
npm install -g eas-cli
```

2. Login to your Expo account

```bash
eas login
```

3.

```bash
eas build --profile development --platform android
```
