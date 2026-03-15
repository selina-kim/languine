import { COLORS } from "@/constants/colors";
import React from "react";
import Svg, { Path } from "react-native-svg";

export const PlayIcon: React.FC<{
  stroke?: string;
  fill?: string;
}> = ({ stroke = COLORS.icon.outlinePrimary, fill = "transparent" }) => (
  <Svg width="100%" height="100%" viewBox="0 0 20 20" fill="none">
    <Path
      d="M5 3V17L17 10L7 3H5Z"
      fill={fill}
      stroke={fill}
      strokeLinecap="round"
    />
    <Path
      d="M4.1655 4.16547C4.16541 3.8723 4.24268 3.58429 4.3895 3.33053C4.53633 3.07677 4.74751 2.86624 5.00172 2.72021C5.25593 2.57417 5.54418 2.49779 5.83735 2.49879C6.13052 2.49978 6.41824 2.57812 6.67146 2.72588L16.6661 8.5559C16.9184 8.70226 17.1278 8.91226 17.2734 9.1649C17.4191 9.41755 17.4959 9.70399 17.4961 9.99561C17.4964 10.2872 17.4201 10.5738 17.2749 10.8267C17.1297 11.0796 16.9206 11.29 16.6686 11.4368L6.67146 17.2685C6.41824 17.4162 6.13052 17.4945 5.83735 17.4955C5.54418 17.4965 5.25593 17.4202 5.00172 17.2741C4.74751 17.1281 4.53633 16.9176 4.3895 16.6638C4.24268 16.41 4.16541 16.122 4.1655 15.8289V4.16547Z"
      stroke={stroke}
      strokeWidth="2.2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </Svg>
);
