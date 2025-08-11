/// <reference types="vite/client" />
const CHATBOT_NAME = "Devobot";
const POPUP_OPEN_AT_START = true;

const TOKEN_REFRESH_THRESHOLD = 2 * 60 * 1000; // 2 minutes in milliseconds

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;
const API_VERSION = import.meta.env.VITE_API_VERSION;

export {
  API_BASE_URL,
  API_VERSION,
  CHATBOT_NAME,
  POPUP_OPEN_AT_START,
  TOKEN_REFRESH_THRESHOLD
};
