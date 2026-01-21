import { COLORS } from "@/constants/colors";
import { useState } from "react";
import { Pressable, ScrollView, Text, View } from "react-native";

interface DropdownProps {
  value: string;
  options: string[];
  onSelect: (value: string) => void;
  placeholder?: string;
}

export const Dropdown = ({
  value,
  options,
  onSelect,
  placeholder = "Select an option",
}: DropdownProps) => {
  const [isOpen, setIsOpen] = useState(false);

  const handleSelect = (option: string) => {
    onSelect(option);
    setIsOpen(false);
  };

  return (
    <View style={{ zIndex: isOpen ? 2000 : 1 }}>
      <Pressable
        onPress={() => setIsOpen(!isOpen)}
        style={{
          backgroundColor: COLORS.backgroundSecondary,
          borderRadius: 8,
          paddingVertical: 8,
          paddingHorizontal: 12,
          flexDirection: "row",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <Text
          style={{
            color: value ? COLORS.text.secondary : COLORS.text.secondary,
          }}
        >
          {value || placeholder}
        </Text>
        <Text style={{ color: COLORS.text.secondary }}>
          {isOpen ? "▲" : "▼"}
        </Text>
      </Pressable>

      {isOpen && (
        <View
          style={{
            position: "absolute",
            top: "100%",
            left: 0,
            right: 0,
            backgroundColor: COLORS.backgroundSecondary,
            borderRadius: 8,
            marginTop: 4,
            maxHeight: 150,
            shadowOffset: { width: 0, height: 4 },
            shadowOpacity: 0.25,
            shadowRadius: 10,
            overflow: "hidden",
          }}
        >
          <ScrollView>
            {options.map((option) => (
              <Pressable
                key={option}
                onPress={() => handleSelect(option)}
                style={{
                  borderRadius: 8,
                  paddingVertical: 8,
                  paddingHorizontal: 12,
                  backgroundColor:
                    value === option
                      ? COLORS.backgroundTertiary
                      : COLORS.backgroundSecondary,
                }}
              >
                <Text
                  style={{
                    color: COLORS.text.secondary,
                    fontWeight: "normal",
                  }}
                >
                  {option}
                </Text>
              </Pressable>
            ))}
          </ScrollView>
        </View>
      )}
    </View>
  );
};
