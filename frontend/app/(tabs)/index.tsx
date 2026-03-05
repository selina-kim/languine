import { CText } from "@/components/common/CText";
import { RouteButton } from "@/components/common/RouteButton";
import { CardsDueBanner } from "@/components/features/index/CardsDueBanner";
import { LastReviewedDecks } from "@/components/features/index/LastReviewedDecks";
import { ScrollView, View } from "react-native";

type LabelProps = {
  text: string;
};

const Label = ({ text }: LabelProps) => (
  <CText
    variant="title"
    style={{
      textAlign: "left",
      paddingHorizontal: 25,
      paddingTop: 25,
      paddingBottom: 5,
    }}
  >
    {text}
  </CText>
);

export default function Index() {
  return (
    <ScrollView
      style={{
        flex: 1,
        padding: 10,
      }}
    >
      <CardsDueBanner countDueCards={5} />
      <Label text="Last Reviewed Decks" />
      <LastReviewedDecks deckName="Korean Vocab" lastReviewed="2-27-2026" />
      <LastReviewedDecks deckName="French Vocab" lastReviewed="2-22-2026" />
      <LastReviewedDecks deckName="Japanese Vocab" lastReviewed="2-24-2026" />
      <View
        style={{
          marginHorizontal: 50,
          marginVertical: 30,
        }}
      >
        <RouteButton text="View Decks" route="decks" />
      </View>
    </ScrollView>
  );
}
