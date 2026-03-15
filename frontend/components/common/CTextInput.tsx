import { COLORS } from "@/constants/colors";
import {
  TextInput as RNTextInput,
  TextInputProps as RNTextInputProps,
  StyleSheet,
  View,
} from "react-native";
import { CText, fonts, textVariants } from "./CText";

const inputBaseStyle = StyleSheet.create({
  base: {
    borderRadius: 8,
    paddingVertical: 8,
    paddingHorizontal: 12,
    outlineColor: COLORS.accent.primary,
    ...fonts.base,
    ...textVariants.base,
  },
});

const inputVariants = StyleSheet.create({
  form: {
    backgroundColor: COLORS.background.secondary,
  },
  editModal: {
    backgroundColor: COLORS.background.primary,
    borderWidth: 2,
    borderColor: COLORS.icon.outlineTertiary,
    fontSize: 18,
  },
});

type InputVariantType = keyof typeof inputVariants;

interface TextInputProps extends RNTextInputProps {
  label?: string;
  value: string;
  onChangeText: (text: string) => void;
  placeholder?: string;
  variant?: InputVariantType;
}

export const CTextInput = ({
  label,
  value,
  onChangeText,
  placeholder,
  variant = "form",
  multiline,
  numberOfLines,
  style,
  ...props
}: TextInputProps) => {
  return (
    <View>
      {label && <CText variant="inputLabel">{label}</CText>}
      <RNTextInput
        value={value}
        onChangeText={onChangeText}
        placeholder={placeholder}
        placeholderTextColor={COLORS.text.tertiary}
        multiline={multiline}
        numberOfLines={numberOfLines}
        style={[
          inputBaseStyle.base,
          inputVariants[variant],
          multiline && {
            minHeight: 80,
            textAlignVertical: "top",
          },
          style,
        ]}
        {...props}
      />
    </View>
  );
};
