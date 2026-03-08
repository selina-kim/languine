import { OpenBookIcon } from "@/assets/icons/OpenBookIcon";
import { CText } from "@/components/common/CText";
import { RouteButton } from "@/components/common/RouteButton";
import { COLORS } from "@/constants/colors";
import { SHADOWS } from "@/constants/shadows";
import React from "react";
import { View } from "react-native";

type CardsDueBannerProps = {
  countDueCards: number;
};

export const CardsDueBanner = ({ countDueCards }: CardsDueBannerProps) => {
  return (
    <View style={{ width: "100%" }}>
      <View
        style={{
          rowGap: 10,
          paddingTop: 30,
          paddingHorizontal: 25,
        }}
      >
        <View
          style={{
            padding: 25,
            borderWidth: 3,
            borderColor: COLORS.icon.outlineSecondary,
            backgroundColor: COLORS.backgroundSecondary,
            borderRadius: 16,
            ...SHADOWS.default,
          }}
        >
          <View
            style={{
              flexDirection: "row",
              marginBottom: 20,
              alignItems: "center",
            }}
          >
            <View
              style={[
                {
                  width: 50,
                  height: 50,
                  borderRadius: 12,
                  borderWidth: 2,
                  borderColor: COLORS.icon.outlineSecondary,
                  backgroundColor: COLORS.icon.fillPrimary,
                  justifyContent: "center",
                  alignItems: "center",
                  flexShrink: 0,
                },
              ]}
            >
              <View
                style={[
                  {
                    width: 28,
                  },
                ]}
              >
                <OpenBookIcon
                  stroke={COLORS.icon.outlineSecondary}
                  fill={COLORS.icon.fillSecondary}
                />
              </View>
            </View>
            <View style={{ marginLeft: 12, flex: 1 }}>
              <CText
                style={{
                  fontSize: 24,
                  lineHeight: 28,
                }}
                bold
              >
                {countDueCards} Cards Due!
              </CText>
              <CText style={{ color: COLORS.text.secondary }}>
                Review your flashcards
              </CText>
            </View>
          </View>
          <RouteButton text="Start Studying" route="revision" />
        </View>
      </View>
    </View>
  );
};
