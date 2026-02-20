import { COLORS } from "@/constants/colors";
import React from "react";
import { StyleSheet, Text, TextProps } from "react-native";

type VariantType = keyof typeof variants;

export interface CTextProps extends TextProps {
  variant?: VariantType;
  bold?: boolean;
}

export const CText: React.FC<CTextProps> = ({
  variant = "base",
  bold = false,
  children,
  style,
  ...props
}) => {
  return (
    <Text
      style={[bold ? fonts.bold : fonts.base, variants[variant], style]}
      {...props}
    >
      {children}
    </Text>
  );
};

const fonts = StyleSheet.create({
  base: {
    fontFamily: "Arimo_400Regular",
  },
  bold: {
    fontFamily: "Arimo_700Bold",
  },
});

const variants = StyleSheet.create({
  base: { color: COLORS.text.primary, fontSize: 16, lineHeight: 24 },
  inputLabel: {
    color: COLORS.text.primary,
    marginBottom: 8,
    fontSize: 16,
    lineHeight: 24,
    ...fonts.bold,
  },
});
