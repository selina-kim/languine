import { COLORS } from "@/constants/colors";
import React from "react";
import { StyleSheet, Text, TextProps } from "react-native";

type TextVariantType = keyof typeof textVariants;

export interface CTextProps extends TextProps {
  variant?: TextVariantType;
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
      style={[bold ? fonts.bold : fonts.base, textVariants[variant], style]}
      {...props}
    >
      {children}
    </Text>
  );
};

export const fonts = StyleSheet.create({
  base: {
    fontFamily: "Arimo_400Regular",
  },
  bold: {
    fontFamily: "Arimo_700Bold",
  },
});

export const textVariants = StyleSheet.create({
  base: { color: COLORS.text.primary, fontSize: 16, lineHeight: 24 },
  inputLabel: {
    color: COLORS.text.primary,
    marginBottom: 8,
    fontSize: 16,
    lineHeight: 24,
    ...fonts.bold,
  },
  containerLabel: {
    color: COLORS.text.primary,
    fontSize: 18,
    lineHeight: 24,
  },
  title: {
    color: COLORS.text.secondary,
    fontSize: 18,
    lineHeight: 28,
    ...fonts.bold,
  },
});
