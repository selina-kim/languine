import { RelativePathString, useRouter } from "expo-router";
import { CButton } from "./CButton";

type RouteButtonProps = {
  text: string;
  route: "index" | "decks" | "revision" | "help" | "settings";
};

export const RouteButton = ({ text, route }: RouteButtonProps) => {
  const router = useRouter();

  const buildRoute = (page: string): RelativePathString => {
    return `${page}` as RelativePathString;
  };

  return (
    <CButton
      variant="primary"
      label={text}
      onPress={() => router.push(buildRoute(route))}
    />
  );
};
