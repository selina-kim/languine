import { COLORS } from "@/constants/colors";
import React from "react";
import { Path, Svg } from "react-native-svg";

export const OpenBookIcon: React.FC<{
  stroke?: string;
  fill?: string;
  strokeWidth?: number;
}> = ({
  stroke = COLORS.icon.outlinePrimary,
  fill = COLORS.icon.fillPrimary,
  strokeWidth = 2,
}) => (
  <Svg width="100%" height="100%" viewBox="0 0 26 26" fill="none">
    <Path
      d="M3.23361 19.5C2.94775 19.5 2.67359 19.3859 2.47146 19.1827C2.26932 18.9795 2.15576 18.704 2.15576 18.4167V4.33333C2.15576 4.04602 2.26932 3.77047 2.47146 3.5673C2.67359 3.36414 2.94775 3.25 3.23361 3.25H8.62285C9.7663 3.25 10.8629 3.70655 11.6715 4.5192C12.48 5.33186 12.9342 6.43406 12.9342 7.58333C12.9342 6.43406 13.3885 5.33186 14.197 4.5192C15.0056 3.70655 16.1022 3.25 17.2456 3.25H22.6349C22.9207 3.25 23.1949 3.36414 23.397 3.5673C23.5992 3.77047 23.7127 4.04602 23.7127 4.33333V18.4167C23.7127 18.704 23.5992 18.9795 23.397 19.1827C23.1949 19.3859 22.9207 19.5 22.6349 19.5H16.1678C15.3102 19.5 14.4877 19.8424 13.8813 20.4519C13.2749 21.0614 12.9342 21.888 12.9342 22.75C12.9342 21.888 12.5936 21.0614 11.9872 20.4519C11.3808 19.8424 10.5583 19.5 9.7007 19.5H3.23361Z"
      stroke={stroke}
      fill={fill}
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <Path
      d="M10.9443 4C12.5827 6.44072 13.4642 6.40285 14.9241 4"
      stroke={stroke}
    />
    <Path
      d="M12.9341 7.5835V22.7502"
      stroke={stroke}
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </Svg>
);
