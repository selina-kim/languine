import { DecksIcon } from "@/assets/icons/DecksIcon";
import { PlusIcon } from "@/assets/icons/PlusIcon";
import { CText } from "@/components/common/CText";
import { COLORS } from "@/constants/colors";
import { useState } from "react";
import { Pressable, View } from "react-native";




export const ListContainer = () => {
  return (
    <View style={{ width: "100%" }}>
      <View
        style={{
          rowGap: "10px",
          paddingVertical: 10,
          paddingHorizontal: 25,
        }}
      >
        <View style={{ 
          paddingVertical: 30,
          paddingHorizontal: 30,
          borderWidth: 2,
          borderColor: COLORS.icon.outlinePrimary,
          borderRadius: 16,}}
        >
          <CText style={{paddingBottom: 10}} bold>
            Tips for Effective Learning
          </CText>
        </View>
      </View>
    </View>
  );
};
