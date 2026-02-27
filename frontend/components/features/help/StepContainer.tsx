import { PlusIcon } from "@/assets/icons/PlusIcon";
import { DecksIcon } from "@/assets/icons/DecksIcon";
import { OpenBookIcon } from "@/assets/icons/OpenBookIcon";
import { CText } from "@/components/common/CText";
import { COLORS } from "@/constants/colors";
import { useState } from "react";
import { Pressable, View } from "react-native";
import { PlusFilledIcon } from "@/assets/icons/PlusFilledIcon";

export const StepContainer = () => {
  return (
    <View style={{ width: "100%" }}>
      <View
        style={{
          rowGap: "10px",
          paddingVertical: 10,
          paddingHorizontal: 25,
        }}
      >
        <View
          style={{
            paddingVertical: 30,
            paddingHorizontal: 30,
            borderWidth: 2,
            borderColor: COLORS.icon.outlinePrimary,
            borderRadius: 16,
          }}
        >
          <View style={{ flexDirection: "row", marginBottom: 20 }}>
            <View
              style={{
                marginTop: 5,
                width: 40,
                height: 40,
                borderRadius: 14,
                backgroundColor: COLORS.icon.outlineSecondary,
              }}
            />
            <View
              style={{
                position: "absolute",
                width: 30,
                top: 10,
                left: 5,
              }}
            >
              <DecksIcon />
            </View>
            <View style={{ marginLeft: 10}}>
              <CText bold>
                Create a Deck
              </CText>
              <CText style={{color: COLORS.text.secondary}}>
                Step 1
              </CText>
            </View>
          </View>
          <CText style={{color: COLORS.text.secondary}}>
            Start by creating a new deck for the language you want to learn. Choose a name, select your language, and add a description.
          </CText>
        </View>
      </View>
    </View>
  );
};
