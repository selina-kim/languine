import { COLORS } from "@/constants/colors";
import React from "react";
import Svg, { Path } from "react-native-svg";

export const PlusIcon: React.FC<{ stroke?: string }> = ({
  stroke = COLORS.text.primary,
}) => (
  <Svg width="16" height="16" viewBox="0 0 16 16" fill="none">
    <Path
      d="M3.33228 7.99756H12.663"
      stroke={stroke}
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <Path
      d="M7.9978 3.33252V12.6632"
      stroke={stroke}
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </Svg>
);
