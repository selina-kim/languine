import { COLORS } from "@/constants/colors";
import { ReactNode } from "react";
import { Modal as RNModal, View } from "react-native";
import { ButtonVariantType, CButton } from "./CButton";
import { CText } from "./CText";

interface ModalProps {
  visible: boolean;
  header: string;
  subheader?: string;
  children?: ReactNode;
  onSubmit?: () => void;
  submitLabel?: string;
  submitVariant?: ButtonVariantType;
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
  submitVariant = "primary",
  onClose,
  closeLabel = "Cancel",
}: ModalProps) => {
  const Buttons = (
    <View style={{ rowGap: 8 }}>
      {onSubmit && (
        <CButton
          onPress={onSubmit}
          variant={submitVariant}
          label={submitLabel}
          style={{ width: "100%" }}
        />
      )}
      {onClose && (
        <CButton
          variant="secondary"
          label={closeLabel}
          onPress={onClose}
          style={{ width: "100%" }}
        />
      )}
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
            backgroundColor: COLORS.background.primary,
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
