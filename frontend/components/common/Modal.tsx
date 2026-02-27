import { COLORS } from "@/constants/colors";
import { ReactNode } from "react";
import { Pressable, Modal as RNModal, StyleSheet, View } from "react-native";
import { CText } from "./CText";

interface ModalProps {
  visible: boolean;
  header: string;
  subheader?: string;
  children: ReactNode;
  onSubmit?: () => void;
  submitLabel?: string;
  onClose: () => void;
  closeLabel?: string;
}

export const Modal = ({
  visible,
  header,
  subheader,
  children,
  onSubmit,
  submitLabel = "Submit",
  onClose,
  closeLabel = "Cancel",
}: ModalProps) => {
  const Buttons = (
    <View style={{ rowGap: 8 }}>
      {onSubmit && (
        <Pressable
          onPress={onSubmit}
          style={[
            buttonStyles.base,
            {
              backgroundColor: COLORS.button.fillPrimary,
            },
          ]}
        >
          <CText bold>{submitLabel}</CText>
        </Pressable>
      )}
      <Pressable
        onPress={onClose}
        style={[
          buttonStyles.base,
          {
            backgroundColor: COLORS.backgroundPrimary,
            borderColor: COLORS.text.primary,
            borderWidth: 2,
          },
        ]}
      >
        <CText bold>{closeLabel}</CText>
      </Pressable>
    </View>
  );

  return (
    <RNModal visible={visible} transparent onRequestClose={onClose}>
      <View
        style={{
          flex: 1,
          backgroundColor: "rgba(0, 0, 0, 0.5)",
          justifyContent: "center",
          alignItems: "center",
        }}
      >
        <View
          style={{
            backgroundColor: COLORS.backgroundPrimary,
            borderRadius: 12,
            padding: 20,
            width: "80%",
            maxWidth: 400,
          }}
        >
          <View style={{ marginBottom: 16, rowGap: 4 }}>
            <CText
              style={{
                fontSize: 20,
                textAlign: "center",
              }}
              bold
            >
              {header}
            </CText>
            {subheader && (
              <CText
                style={{
                  color: COLORS.text.secondary,
                  textAlign: "center",
                }}
              >
                {subheader}
              </CText>
            )}
          </View>
          <View style={{ zIndex: 10 }}>{children}</View>
          {Buttons}
        </View>
      </View>
    </RNModal>
  );
};

const buttonStyles = StyleSheet.create({
  base: {
    height: 32,
    display: "flex",
    justifyContent: "center",
    borderRadius: 8,
    alignItems: "center",
  },
});
