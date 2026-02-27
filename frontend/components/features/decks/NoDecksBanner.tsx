import { DecksIcon } from "@/assets/icons/DecksIcon";
import { PlusIcon } from "@/assets/icons/PlusIcon";
import { CText } from "@/components/common/CText";
import { COLORS } from "@/constants/colors";
import { useState } from "react";
import { Pressable, View } from "react-native";
import { CreateNewDeckModal } from "./CreateNewDeckModal";

export const NoDecksBanner = () => {
  const [modalVisible, setModalVisible] = useState(false);

  return (
    <View style={{ width: "100%", height: "100%" }}>
      <View
        style={{
          display: "flex",
          rowGap: "10px",
          paddingVertical: 30,
        }}
      >
        <View style={{ width: 64, marginHorizontal: "auto" }}>
          <DecksIcon />
        </View>
        <CText
          style={{
            textAlign: "center",
          }}
          bold
        >
          No Decks Yet
        </CText>
        <CText
          style={{
            color: COLORS.text.secondary,
            textAlign: "center",
          }}
        >
          Create your first deck to start learning!
        </CText>
        <Pressable
          onPress={() => setModalVisible(true)}
          style={{
            backgroundColor: COLORS.accent.primary,
            padding: 10,
            borderRadius: 8,
            display: "flex",
            flexDirection: "row",
            marginHorizontal: "auto",
            marginTop: 20,
            columnGap: 5,
            alignItems: "center",
          }}
        >
          <View style={{ minWidth: "auto" }}>
            <PlusIcon />
          </View>
          <CText
            style={{
              textAlign: "center",
              width: "100%",
            }}
            bold
          >
            Create Your First Deck
          </CText>
        </Pressable>
        <CreateNewDeckModal
          visible={modalVisible}
          onClose={() => setModalVisible(false)}
        />
      </View>
    </View>
  );
};
