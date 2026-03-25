import { ChevronDownIcon } from "@/assets/icons/ChevronDownIcon";
import { CText } from "@/components/common/CText";
import { COLORS } from "@/constants/colors";
import { useState } from "react";
import { Pressable, View } from "react-native";

interface FAQItem {
  question: string;
  answer: string;
}

interface FAQProps {
  faqs: FAQItem[];
}

export const FAQ = ({ faqs }: FAQProps) => {
  const [openIndexes, setOpenIndexes] = useState<number[]>([]);

  const toggle = (index: number) => {
    setOpenIndexes((prev) =>
      prev.includes(index) ? prev.filter((i) => i !== index) : [...prev, index],
    );
  };

  return (
    <View style={{ width: "100%" }}>
      <View
        style={{
          paddingBottom: 25,
          paddingHorizontal: 25,
        }}
      >
        {faqs.map((item, index) => {
          const isOpen = openIndexes.includes(index);

          return (
            <View
              key={index}
              style={{
                borderBottomWidth: 1,
                borderBottomColor: COLORS.icon.outlinePrimary,
                paddingVertical: 16,
              }}
            >
              <Pressable
                onPress={() => toggle(index)}
                style={{
                  flexDirection: "row",
                  justifyContent: "space-between",
                  columnGap: 2,
                  alignItems: "center",
                }}
              >
                <CText>{item.question}</CText>
                <View
                  style={{
                    transform: [{ rotate: isOpen ? "180deg" : "0deg" }],
                    width: 16,
                    height: 16,
                  }}
                >
                  <ChevronDownIcon stroke={COLORS.text.primary} />
                </View>
              </Pressable>

              {isOpen && (
                <View style={{ marginTop: 10 }}>
                  <CText style={{ color: COLORS.text.secondary }}>
                    {item.answer}
                  </CText>
                </View>
              )}
            </View>
          );
        })}
      </View>
    </View>
  );
};
