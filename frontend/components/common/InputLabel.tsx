import { COLORS } from "@/constants/colors";
import { StyleSheet, Text } from "react-native";

interface InputLabelProps {
  children: string;
}

export const InputLabel = ({ children }: InputLabelProps) => {
  return <Text style={styles.label}>{children}</Text>;
};

const styles = StyleSheet.create({
  label: {
    color: COLORS.text.primary,
    marginBottom: 8,
    fontWeight: "bold",
  },
});
