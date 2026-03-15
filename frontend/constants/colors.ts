const lightTheme = {
  background: {
    primary: "#FFFCF9",
    secondary: "#FFF5DB",
    tertiary: "#FCE6B1",
  },
  icon: {
    outlinePrimary: "#8D481C",
    outlineSecondary: "#FFBA26",
    outlineTertiary: "#5C2C0E",
    fillPrimary: "#FFFCF9",
    fillSecondary: "#FFF5DB",
  },
  text: {
    primary: "#5C2C0E",
    secondary: "#8D481C",
    tertiary: "#bc8b63",
    error: "#D41605",
    white: "#FFFCF9",
    language: "#FF8B25",
  },
  accent: {
    primary: "#FFBA26",
    secondary: "#399BEB",
    delete: "#D41605",
  },
  button: {
    fillPrimary: "#FFBA26",
    fillSecondary: "#FFFCF9",
    outlinePrimary: "#8D481C",
  },
} as const;

export const THEMES = {
  light: lightTheme,
} as const;

// temporary for now
export const COLORS = THEMES.light;
