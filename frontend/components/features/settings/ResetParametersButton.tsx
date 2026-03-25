import { CButton } from "@/components/common/CButton";
import { Modal } from "@/components/common/Modal";
import { useState } from "react";

export const ResetParametersButton = () => {
  const [isDeleteModalVisible, setIsDeleteModalVisible] = useState(false);

  const handleConfirm = () => {
    // TODO
    console.log("parameters have been reset");
  };

  return (
    <>
      <CButton
        variant="criticalSecondary"
        label="Delete Account"
        onPress={() => setIsDeleteModalVisible(true)}
        style={{
          marginVertical: 20,
        }}
      />
      <Modal
        visible={isDeleteModalVisible}
        header="Are you sure?"
        submitLabel="Reset Parameters"
        subheader="This action will reset all optimization parameters to their default values"
        submitVariant="criticalSecondary"
        closeLabel="Cancel"
        onClose={() => setIsDeleteModalVisible(false)}
        onSubmit={handleConfirm}
      />
    </>
  );
};
