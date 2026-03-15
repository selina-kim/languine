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
    columnGap: 5,
    alignItems: "center",
    justifyContent: "center",
  },
});

const buttonVariants = StyleSheet.create({
  primary: {
    backgroundColor: COLORS.accent.primary,
  },
  secondary: {
    backgroundColor: COLORS.backgroundPrimary,
    borderColor: COLORS.text.primary,
    borderWidth: 2,
  },
  deletePrimary: {
    backgroundColor: COLORS.accent.delete,
  },
  deleteSecondary: {
    backgroundColor: COLORS.backgroundPrimary,
    borderColor: COLORS.accent.delete,
    borderWidth: 2,
  },
});

const buttonTextProps: { [variant: string]: CTextProps } = {
  primary: {
    bold: true,
  },
  secondary: {
    bold: true,
  },
  deletePrimary: {
    bold: false,
    style: { color: COLORS.text.white },
  },
  deleteSecondary: {
    bold: false,
    style: { color: COLORS.accent.delete },
  },
};

type ButtonVariantType = keyof typeof buttonVariants;

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
              buttonVariants[variant],
              style(state),
            ]
          : [buttonBaseStyle.base, buttonVariants[variant], style]
      }
      {...props}
    >
      {Icon && <View style={{ minWidth: "auto" }}>{Icon}</View>}
      <CText
        style={{
          textAlign: "center",
        }}
        {...buttonTextProps[variant]}
      >
        {label}
      </CText>
    </Pressable>
  );
};
