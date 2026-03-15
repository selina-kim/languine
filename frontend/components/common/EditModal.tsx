import { CTextInput } from "@/components/common/CTextInput";
import { Modal } from "@/components/common/Modal";
import React from "react";

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
      <CTextInput
        value={value}
        onChangeText={onChange}
        variant="editModal"
        style={{ marginTop: 10, marginBottom: 20 }}
      />
    </Modal>
  );
};

export default EditModal;
