import { Modal } from "@/components/common/Modal";
import { COLORS } from "@/constants/colors";
import React from "react";
import { TextInput } from "react-native";

interface EditModalProps {
  visible: boolean;
  header: string;
  subheader?: string;
  value: string;
  onChange: (v: string) => void;
  onClose: () => void;
  onSave: () => void;
  submitLabel?: string;
  closeLabel?: string;
}

export const EditModal: React.FC<EditModalProps> = ({
  visible,
  header,
  subheader,
  value,
  onChange,
  onClose,
  onSave,
  submitLabel = "Save",
  closeLabel = "Cancel",
}) => {
  return (
    <Modal
      visible={visible}
      header={header}
      subheader={subheader}
      onClose={onClose}
      onSubmit={onSave}
      submitLabel={submitLabel}
      closeLabel={closeLabel}
    >
      <TextInput
        value={value}
        onChangeText={onChange}
        style={{
          borderWidth: 2,
          borderColor: COLORS.icon.outlineTertiary,
          borderRadius: 8,
          padding: 10,
          marginTop: 10,
          marginBottom: 20,
          fontSize: 20,
          color: COLORS.text.primary,
        }}
      />
    </Modal>
  );
};

export default EditModal;
