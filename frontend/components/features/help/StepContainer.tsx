import { CText } from "@/components/common/CText";
import { COLORS } from "@/constants/colors";
import React, { ReactNode } from "react";
import { StyleProp, View, ViewStyle } from "react-native";

type StepContainerProps = {
  title: string;
  step: string;
  description: string;
  Icon: ReactNode;
  iconStyle?: StyleProp<ViewStyle>;
};

export const StepContainer = ({
  title,
  step,
  description,
  Icon,
  iconStyle,
}: StepContainerProps) => {
  return (
    <View style={{ width: "100%" }}>
      <View
        style={{
          rowGap: 10,
          paddingVertical: 10,
          paddingHorizontal: 25,
        }}
      >
        <View
          style={{
            padding: 25,
            borderWidth: 2,
            borderColor: COLORS.icon.outlinePrimary,
            borderRadius: 16,
          }}
        >
          <View style={{ flexDirection: "row", marginBottom: 20 }}>
            <View
              style={[
                {
                  marginTop: 5,
                  width: 40,
                  height: 40,
                  borderRadius: 14,
                  backgroundColor: COLORS.icon.outlineSecondary,
                  justifyContent: "center",
                  alignItems: "center",
                },
              ]}
            >
              <View
                style={[
                  {
                    width: 24,
                  },
                  iconStyle,
                ]}
              >
                {Icon}
              </View>
            </View>
            <View style={{ marginLeft: 10 }}>
              <CText variant="containerLabel" bold>
                {title}
              </CText>
              <CText style={{ color: COLORS.text.secondary }}>{step}</CText>
            </View>
          </View>

          <CText style={{ color: COLORS.text.secondary }}>{description}</CText>
        </View>
      </View>
    </View>
  );
};
