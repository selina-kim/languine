import { COLORS } from "@/constants/colors";
import { ReactNode } from "react";
import { Pressable, PressableProps, StyleSheet, View } from "react-native";
import { CText, CTextProps } from "./CText";

const buttonBaseStyle = StyleSheet.create({
  base: {
    paddingHorizontal: 12,
    height: 40,
    borderRadius: 8,
    display: "flex",
    flexDirection: "row",
    columnGap: 8,
    alignItems: "center",
    justifyContent: "center",
  },
});

const buttonVariants = StyleSheet.create({
  primary: {
    backgroundColor: COLORS.accent.primary,
  },
  secondary: {
    backgroundColor: COLORS.background.primary,
    borderColor: COLORS.text.primary,
    borderWidth: 2,
  },
  google: {
    height: 50,
    backgroundColor: COLORS.button.fillSecondary,
    borderColor: COLORS.button.outlinePrimary,
    borderWidth: 2,
  },
  criticalPrimary: {
    backgroundColor: COLORS.accent.delete,
  },
  criticalSecondary: {
    backgroundColor: COLORS.background.primary,
    borderColor: COLORS.accent.delete,
    borderWidth: 2,
  },
});

const buttonTextProps: { [buttonTextVariant: string]: CTextProps } = {
  primary: {
    bold: true,
  },
  secondary: {
    bold: true,
  },
  google: {
    variant: "google",
  },
  criticalPrimary: {
    bold: true,
    style: { color: COLORS.text.white },
  },
  criticalSecondary: {
    bold: true,
    style: { color: COLORS.accent.delete },
  },
};

export type ButtonVariantType = keyof typeof buttonVariants;

interface CButtonProps extends PressableProps {
  variant: ButtonVariantType;
  label: string;
  Icon?: ReactNode;
}

export const CButton: React.FC<CButtonProps> = ({
  variant,
  label,
  Icon,
  style,
  ...props
}) => {
  return (
    <Pressable
      style={
        typeof style === "function"
          ? (state) => [
              buttonBaseStyle.base,
              variant && buttonVariants[variant],
              style(state),
            ]
          : [buttonBaseStyle.base, variant && buttonVariants[variant], style]
      }
      {...props}
    >
      {Icon && <View style={{ width: 16, height: 16 }}>{Icon}</View>}
      <CText
        style={{
          textAlign: "center",
        }}
        {...(variant && buttonTextProps[variant])}
      >
        {label}
      </CText>
    </Pressable>
  );
};
