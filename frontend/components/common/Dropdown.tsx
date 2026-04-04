import { ChevronDownIcon } from "@/assets/icons/ChevronDownIcon";
import { COLORS } from "@/constants/colors";
import { useState } from "react";
import { Pressable, ScrollView, View } from "react-native";
import { CText } from "./CText";

interface DropdownProps {
  value: string | null;
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
    <View>
      <Pressable
        onPress={() => setIsOpen(!isOpen)}
        style={{
          backgroundColor: COLORS.background.secondary,
          borderRadius: 8,
          paddingVertical: 8,
          paddingHorizontal: 12,
          flexDirection: "row",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <CText style={!value && { color: COLORS.text.tertiary }}>
          {value || placeholder}
        </CText>
        <View
          style={{
            opacity: 0.5,
            width: 16,
            height: 16,
            transform: [{ rotate: isOpen ? "180deg" : "0deg" }],
          }}
        >
          <ChevronDownIcon stroke={COLORS.text.primary} />
        </View>
      </Pressable>
      {isOpen && (
        <ScrollView
          style={{
            position: "absolute",
            flex: 1,
            top: "100%",
            left: 0,
            right: 0,
            marginTop: 4,
            backgroundColor: COLORS.background.secondary,
            borderRadius: 8,
            maxHeight: 140,
          }}
        >
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
                    ? COLORS.background.tertiary
                    : COLORS.background.secondary,
              }}
            >
              <CText
                style={{
                  color: COLORS.text.secondary,
                  fontWeight: "normal",
                }}
              >
                {option}
              </CText>
            </Pressable>
          ))}
        </ScrollView>
      )}
    </View>
  );
};
