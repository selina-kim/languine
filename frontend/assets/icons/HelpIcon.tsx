import { COLORS } from "@/constants/colors";
import React from "react";
import { Svg, Path, Ellipse } from "react-native-svg";

export const HelpIcon: React.FC<{
  stroke?: string;
  fill?: string;
}> = ({
  stroke = COLORS.icon.outlinePrimary,
  fill = COLORS.icon.fillPrimary,
}) => (
  <Svg width="100%" height="100%" viewBox="0 0 23 23" fill="none">
    <Ellipse cx="11.4417" cy="11.5" rx="10.4468" ry="10.5" fill={fill} />
    <Path
      d="M11.4418 21.0832C16.7077 21.0832 20.9766 16.7926 20.9766 11.4998C20.9766 6.20711 16.7077 1.9165 11.4418 1.9165C6.17586 1.9165 1.90698 6.20711 1.90698 11.4998C1.90698 16.7926 6.17586 21.0832 11.4418 21.0832Z"
      stroke={stroke}
      strokeWidth="1.99944"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <Path
      d="M8.66724 8.62506C8.8914 7.98457 9.33386 7.44449 9.91625 7.10048C10.4986 6.75646 11.1834 6.63071 11.8492 6.74549C12.515 6.86027 13.1189 7.20819 13.5539 7.72761C13.9889 8.24703 14.227 8.90443 14.226 9.58339C14.226 11.5001 11.3656 12.4584 11.3656 12.4584"
      stroke={stroke}
      strokeWidth="1.99944"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <Path
      d="M11.4417 16.2915H11.4525"
      stroke={stroke}
      strokeWidth="1.99944"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </Svg>
);
