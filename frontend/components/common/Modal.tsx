import { COLORS } from "@/constants/colors";
import { ReactNode } from "react";
import { Pressable, Modal as RNModal, Text, View } from "react-native";

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
          style={{
            backgroundColor: COLORS.button.fillPrimary,
            paddingVertical: 12,
            borderRadius: 8,
            alignItems: "center",
          }}
        >
          <Text
            style={{
              color: COLORS.text.primary,
              fontWeight: "bold",
            }}
          >
            {submitLabel}
          </Text>
        </Pressable>
      )}
      <Pressable
        onPress={onClose}
        style={{
          backgroundColor: COLORS.backgroundPrimary,
          paddingVertical: 12,
          borderRadius: 8,
          alignItems: "center",
          borderColor: COLORS.text.primary,
          borderWidth: 2,
        }}
      >
        <Text
          style={{
            color: COLORS.text.primary,
            fontWeight: "bold",
          }}
        >
          {closeLabel}
        </Text>
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
            <Text
              style={{
                fontSize: 20,
                fontWeight: "bold",
                textAlign: "center",
                color: COLORS.text.primary,
              }}
            >
              {header}
            </Text>
            {subheader && (
              <Text
                style={{
                  color: COLORS.text.secondary,
                  textAlign: "center",
                }}
              >
                {subheader}
              </Text>
            )}
          </View>
          <View style={{ zIndex: 10 }}>{children}</View>
          {Buttons}
        </View>
      </View>
    </RNModal>
  );
};
