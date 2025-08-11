const STORAGE_KEY = "tokenData";

export interface TokenData {
  accessToken: string;
  refreshToken: string;
  accessTokenExpiry: number;
}

export function setTokenData(
  accessToken: string,
  refreshToken: string,
  expiresIn: number
) {
  const expiryTime = Date.now() + expiresIn * 1000;
  const data: TokenData = {
    accessToken,
    refreshToken,
    accessTokenExpiry: expiryTime
  };
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(data));
}

export function getTokenData(): TokenData | null {
  const raw = sessionStorage.getItem(STORAGE_KEY);
  return raw ? JSON.parse(raw) : null;
}

export function clearTokenData() {
  sessionStorage.removeItem(STORAGE_KEY);
}
