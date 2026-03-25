import { CButton } from "@/components/common/CButton";
import { Modal } from "@/components/common/Modal";
import { useState } from "react";

export const DeleteAccountButton = () => {
  const [isDeleteModalVisible, setIsDeleteModalVisible] = useState(false);

  const handleConfirm = () => {
    // TODO
    console.log("deleted account");
  };

  return (
    <>
      <CButton
        variant="criticalPrimary"
        label="Delete Account"
        onPress={() => setIsDeleteModalVisible(true)}
        style={{
          marginTop: 40,
          marginBottom: 20,
        }}
      />
      <Modal
        visible={isDeleteModalVisible}
        header="Are you sure?"
        submitLabel="Delete Account"
        subheader="This action will permanently delete your account and all associated data"
        submitVariant="criticalPrimary"
        closeLabel="Cancel"
        onClose={() => setIsDeleteModalVisible(false)}
        onSubmit={handleConfirm}
      />
    </>
  );
};
