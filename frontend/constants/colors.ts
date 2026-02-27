const lightTheme = {
  backgroundPrimary: "#FFFCF9",
  backgroundSecondary: "#FFF5DB",
  backgroundTertiary: "#FCE6B1",
  icon: {
    outlinePrimary: "#8D481C",
    outlineSecondary: "#FFBA26",
    fillPrimary: "#FFFCF9",
    fillSecondary: "#FFF5DB",
  },
  text: {
    primary: "#5C2C0E",
    secondary: "#8D481C",
    tertiary: "#bc8b63",
  },
  accent: {
    primary: "#FFBA26",
    secondary: "#399BEB",
    delete: "#D41605",
  },
  button: {
    fillPrimary: "#FFBA26",
    fillSecondary: "#FFFCF9",
  },
} as const;

export const THEMES = {
  light: lightTheme,
} as const;

// temporary for now
export const COLORS = THEMES.light;
