import React, { useState } from "react";
import { View } from "react-native";
import { CButton } from "./CButton";
import { Modal } from "./Modal";

interface DeleteButtonProps {
  label?: string;
  onConfirm: () => void;
  deleteVariant?: "deletePrimary" | "deleteSecondary";
  confirmMessage?: string;
  confirmDescription?: string;
  submitLabel?: string;
}

export const DeleteButton: React.FC<DeleteButtonProps> = ({
  label = "Delete",
  onConfirm,
  confirmMessage = "Are you sure?",
  confirmDescription = "This action cannot be undone",
  submitLabel = "Delete",
  deleteVariant = "deletePrimary",
}) => {
  const [modalVisible, setModalVisible] = useState(false);

  const handleConfirm = () => {
    setModalVisible(false);
    onConfirm();
  };

  return (
    <>
      <CButton
        variant={deleteVariant}
        label={label}
        onPress={() => setModalVisible(true)}
      />

      <Modal
        visible={modalVisible}
        header={confirmMessage}
        subheader={confirmDescription}
        onClose={() => setModalVisible(false)}
        onSubmit={handleConfirm}
        submitLabel={submitLabel}
        submitVariant={deleteVariant}
        closeLabel="Cancel"
      >
        <View />
      </Modal>
    </>
  );
};

export default DeleteButton;
