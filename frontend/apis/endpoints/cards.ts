import client from "../client";

// TODO
export const getCards = () => client.get("");

// TODO
export const createCard = () => client.post("", null);

// TODO
export const updateCard = () => client.put("", null);

export default { getCards, createCard, updateCard };
