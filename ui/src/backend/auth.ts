import { API_BASE_URL, TOKEN_REFRESH_THRESHOLD } from '../constants';
import { getTokenData, setTokenData } from '../utils';

type OAuthToken = {
  access_token: string
  expires_in: number
  refresh_token: string
  token_type: "bearer"
  scope: string | null
}

async function getUserToken(): Promise<string> {
    // read from the url query parameters
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get("token");
    if (!token) {
        return "token";
    }
    return token;
}

async function getAccessToken(): Promise<OAuthToken> {
    const url = `${API_BASE_URL}/token`;
    const headers = new Headers({
        'Content-Type': 'application/x-www-form-urlencoded',
    });
    const body = new URLSearchParams({
        token: await getUserToken(),
        grant_type: "authorization_code",
    });

    return (
         fetch(url, {
            method: 'POST',
            headers: headers,
            body: body,
        })
        .then((response) => {
            if (!response.ok) {
                throw new Error(
                    `Status code: ${response.status}
                    Response: ${response.statusText}`
                );
            }
            return response.json();
        })
        .then((data) => {
            const tokenData = data as OAuthToken;
            return tokenData;
        })
    );
}

async function refreshAccessToken(refreshToken: string): Promise<OAuthToken> {
    const url = `${API_BASE_URL}/token`;
    const headers = new Headers({
        'Content-Type': 'application/x-www-form-urlencoded',
    });
    const body = new URLSearchParams({
        token: refreshToken,
        grant_type: "refresh_token",
    });

    return (
         fetch(url, {
            method: 'POST',
            headers: headers,
            body: body,
        })
        .then((response) => {
            if (!response.ok) {
                throw new Error(
                    `Status code: ${response.status}
                    Response: ${response.statusText}`
                );
            }
            return response.json();
        })
        .then((data) => {
            const tokenData = data as OAuthToken;
            if (!tokenData.access_token) {
                throw new Error("No access token found in response");
            }
            return tokenData;
        })
    );
}

export async function getValidAccessToken(): Promise<string> {
  const tokenData = getTokenData();

  // If no data in session storage, fetch a new token
  if (!tokenData) {
    const oauthToken = await getAccessToken();
    setTokenData(
      oauthToken.access_token,
      oauthToken.refresh_token,
      oauthToken.expires_in,
    );
    return oauthToken.access_token;
  }

  // Refresh if < 2 mins left
  else if (tokenData.accessTokenExpiry - Date.now() < TOKEN_REFRESH_THRESHOLD) {
    const oauthToken = await refreshAccessToken(tokenData.refreshToken);
    setTokenData(
      oauthToken.access_token,
      oauthToken.refresh_token,
      oauthToken.expires_in,
    );
    return oauthToken.access_token;
  }

  // If token is still valid, return it
  else {
    return tokenData.accessToken;
  }
}
