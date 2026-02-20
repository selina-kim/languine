import { DecksIcon } from "@/assets/icons/DecksIcon";
import { PlusIcon } from "@/assets/icons/PlusIcon";
import { CButton } from "@/components/common/CButton";
import { CText } from "@/components/common/CText";
import { COLORS } from "@/constants/colors";
import { useState } from "react";
import { View } from "react-native";
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
        <View style={{ width: 64, height: 64, marginHorizontal: "auto" }}>
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
        <CButton
          variant="primary"
          label="Create Your First Deck"
          onPress={() => setModalVisible(true)}
          Icon={<PlusIcon />}
          style={{ marginHorizontal: "auto", marginTop: 20 }}
        />
        <CreateNewDeckModal
          visible={modalVisible}
          onClose={() => setModalVisible(false)}
        />
      </View>
    </View>
  );
};
