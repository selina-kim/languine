import client from "../client";

export interface ReviewLogResponseData {
  card_id: number;
  grade: number;
  review_datetime: string;
  review_duration: number;
}

export interface EndReviewResponseData {
  message: string;
  parameters_optimized: boolean;
}

export interface DueCard {
  card_id: number;
  due_date: string;
  deck_id: number;
}

export interface GetDueCardsResponseData {
  num_due_cards: number;
  due_cards: DueCard[];
}

export const logReview = (
  card_id: number,
  grade: number,
  review_duration: number,
): Promise<{ data: ReviewLogResponseData; error: string | null }> =>
  client.post(`/reviews`, JSON.stringify({
    card_id,
    grade,
    review_duration,
  }));

export const endReview = (
  total_cards_reviewed: number,
): Promise<{
  data: EndReviewResponseData; error: string | null }> =>
  client.post(`/end-review`, JSON.stringify({ total_cards_reviewed }));

export const getDueCards = (): Promise<{
  data: GetDueCardsResponseData;
  error: string | null;
}> => client.get(`/due-cards`);

export const getNumDueCards = (
): Promise<{
  data: { num_due_cards: number }; error: string | null }> => 
  client.get(`/num-due-cards`);

export default {
  logReview,
  endReview,
  getDueCards,
  getNumDueCards,
};

