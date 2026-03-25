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

export default {
  logReview,
  endReview,
};

