import { CButton } from "@/components/common/CButton";
import { Modal } from "@/components/common/Modal";
import { useState } from "react";
import { updateCurrentUser } from "@/apis/endpoints/users";
import { Alert } from "react-native";
import { useAuth } from "@/context/AuthContext";

export const ResetParametersButton = () => {
  const [isDeleteModalVisible, setIsDeleteModalVisible] = useState(false);
  const { user } = useAuth();

  const handleConfirm = () => {
    if (!user) {
      Alert.alert("Reset failed", "You must be logged in to reset parameters.");
      setIsDeleteModalVisible(false);
      return;
    }

    void updateCurrentUser({
      reset_fsrs_params: true,
      // Backend requires at least one "real" field alongside reset_fsrs_params
      display_name: user.name,
    }).then(({ error }) => {
      if (error) {
        Alert.alert("Reset failed", error);
      } else {
        Alert.alert(
          "Parameters reset",
          "Your optimization parameters have been reset to defaults.",
        );
      }
    });
    setIsDeleteModalVisible(false);
  };

  return (
    <>
      <CButton
        variant="criticalSecondary"
        label="Reset Parameters"
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
