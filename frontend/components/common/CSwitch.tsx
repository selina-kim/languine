import React from "react";
import { Pressable, View, StyleSheet } from "react-native";
import { COLORS } from "@/constants/colors";

interface MySwitchProps {
  value: boolean;
  onChange: (next: boolean) => void;
  activeColor?: string;
  inactiveColor?: string;
  thumbColor?: string;
  disabled?: boolean;
}

export function CSwitch({
  value,
  onChange,
  activeColor = COLORS.button.fillPrimary,
  inactiveColor = COLORS.backgroundTertiary,
  thumbColor = "#ffffff",
  disabled = false,
}: MySwitchProps) {
  return (
    <Pressable
      onPress={() => {
        if (disabled) return;
        const next = !value;
        // eslint-disable-next-line no-console
        console.log("CSwitch toggled:", next);
        onChange(next);
      }}
      accessibilityRole="switch"
      accessibilityState={{ checked: value, disabled }}
      style={({ pressed }) => [
        styles.track,
        {
          backgroundColor: value ? activeColor : inactiveColor,
          opacity: pressed ? 0.6 : 1,
        },
        disabled && styles.disabled,
      ]}
    >
      {({ pressed }) => (
        <View
          style={[
            styles.thumb,
            {
              backgroundColor: thumbColor,
              opacity: pressed ? 0.8 : 1,
              transform: [{ scale: pressed ? 0.96 : 1 }],
            },
            value ? styles.thumbOn : styles.thumbOff,
          ]}
        />
      )}
    </Pressable>
  );
}

export default CSwitch;

const styles = StyleSheet.create({
  track: {
    width: 44,
    height: 26,
    borderRadius: 26,
    padding: 3,
    justifyContent: "center",
  },
  thumb: {
    width: 20,
    height: 20,
    borderRadius: 20,
    shadowColor: "#000",
    shadowOpacity: 0.1,
    shadowRadius: 2,
    shadowOffset: { width: 0, height: 1 },
  },
  thumbOn: {
    alignSelf: "flex-end",
  },
  thumbOff: {
    alignSelf: "flex-start",
  },
  disabled: {
    opacity: 0.6,
  },
});
