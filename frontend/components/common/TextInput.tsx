import { COLORS } from "@/constants/colors";
import {
  TextInput as RNTextInput,
  TextInputProps as RNTextInputProps,
  View,
} from "react-native";
import { CText } from "./CText";

interface TextInputProps extends RNTextInputProps {
  label: string;
  value: string;
  onChangeText: (text: string) => void;
  placeholder?: string;
}

export const TextInput = ({
  label,
  value,
  onChangeText,
  placeholder,
  multiline,
  numberOfLines,
  ...props
}: TextInputProps) => {
  return (
    <View>
      <CText variant="inputLabel">{label}</CText>
      <RNTextInput
        value={value}
        onChangeText={onChangeText}
        placeholder={placeholder}
        placeholderTextColor={COLORS.text.tertiary}
        multiline={multiline}
        numberOfLines={numberOfLines}
        style={[
          {
            backgroundColor: COLORS.backgroundSecondary,
            borderRadius: 8,
            paddingVertical: 8,
            paddingHorizontal: 12,
            color: COLORS.text.primary,
            outlineColor: COLORS.accent.primary,
          },
          multiline && {
            minHeight: 80,
            textAlignVertical: "top",
          },
        ]}
        {...props}
      />
    </View>
  );
};
