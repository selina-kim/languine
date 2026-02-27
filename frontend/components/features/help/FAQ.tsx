import { CText } from "@/components/common/CText";
import { COLORS } from "@/constants/colors";
import { useState } from "react";
import { Pressable, View } from "react-native";

const FAQ_DATA = [
  {
    question: "What is spaced repetition?",
    answer:
      "Spaced repetition is a learning technique that involves reviewing information at increasing intervals to improve long-term retention.",
  },
  {
    question: "How should I rate my answers?",
    answer:
      "Rate your answer based on how easily you were able to recall the information:\n\nEasy: you recalled it effortlessly\nGood: you recalled it with some effort\nHard: you recall it with difficulty\nAgain: you could not recall it at all",
  },
  {
    question: "How many cards should I add to a deck?",
    answer:
      "As many as you want!\n\nIt is recommended to add 5-10 cards per day to avoid overwhelming yourself during reviews.\n\nConsistency is key, so find a pace that works for you and stick to it.",
  },
  {
    question: "How often should I review?",
    answer:
      "Daily review is recommended. The system will space cards automatically for optimal retention.",
  },
  {
    question: "Can I edit cards after creating them?",
    answer:
      "Yes. You can edit or delete cards at any time.\n\nTo edit or delete a card, go to the deck page, view the deck that contains card you want to edit, locate the card, and then select the edit or delete icon.",
  },
];

export const FAQ = () => {
  const [openIndexes, setOpenIndexes] = useState<number[]>([]);

  const toggle = (index: number) => {
    setOpenIndexes((prev) =>
      prev.includes(index)
        ? prev.filter((i) => i !== index) // close it
        : [...prev, index] // open it
    );
  };

  return (
    <View style={{ width: "100%" }}>
      <View
        style={{
          rowGap: 10,
          paddingVertical: 10,
          paddingHorizontal: 25,
        }}
      >
        {FAQ_DATA.map((item, index) => {
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
                  alignItems: "center",
                }}
              >
                <CText>{item.question}</CText>

                <CText
                  style={{
                    color: COLORS.text.secondary,
                    fontSize: 18,
                  }}
                >
                  {isOpen ? "−" : "+"}
                </CText>
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