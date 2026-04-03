import client from "@/apis/client";

export interface UpdateUserPayload {
  display_name?: string;
  timezone?: string;
  new_cards_per_day?: number;
  desired_retention?: number; // 0.0 - 1.0
  auto_optimize?: boolean;
  num_reviews_per_optimize?: number;
  reset_fsrs_params?: boolean;
}

export const getCurrentUser = () => client.get(`/users/me`);

export const updateCurrentUser = (data: UpdateUserPayload) =>
  client.put(`/users/me`, JSON.stringify(data));

export const deleteCurrentUser = () => client.delete(`/users/me`);

export default {
  getCurrentUser,
  updateCurrentUser,
  deleteCurrentUser,
};
