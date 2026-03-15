import client from "../client";

export const getTranslation = (
  text: string,
  targetLang: string,
  sourceLang: string,
) =>
  client.get(
    `/translate?text=${text}&target=${targetLang}&source=${sourceLang}`,
  );

export default { getTranslation };
