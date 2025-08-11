import { getValidAccessToken } from "./auth";
import { API_BASE_URL, API_VERSION } from "../constants";

type RequestMethod = "GET" | "POST" | "PUT" | "DELETE" | "PATCH";

export type OrderBy = "ASC" | "DESC";

// Overload: without parseJson, returns Response
export function fetchWithToken(
    options: {
        url: string;
        method: RequestMethod;
        headers?: HeadersInit | null;
        body?: Record<string, unknown> | null;
    }
): Promise<Response>;

// Overload: with parseJson=true, returns parsed JSON of type T
export function fetchWithToken<T>(
    options: {
        url: string;
        method: RequestMethod;
        headers?: HeadersInit | null;
        body?: Record<string, unknown> | null;
        parseJson: true;
    }
): Promise<T>;

// Implementation
export async function fetchWithToken<T = unknown>(
    options: {
        url: string;
        method: RequestMethod;
        headers?: HeadersInit | null;
        body?: Record<string, unknown> | null;
        parseJson?: boolean;
    }
): Promise<Response | T> {
    const { url, method, headers = null, body = null, parseJson = false } = options;
    const accessToken = await getValidAccessToken();

    // Set up headers
    const tokenHeaders = headers ? new Headers(headers) : new Headers();
    tokenHeaders.set("Authorization", `Bearer ${accessToken}`);

    // Always JSON encode body
    let requestBody: string | undefined;
    if (body != null) {
        tokenHeaders.set("Content-Type", "application/json");
        requestBody = JSON.stringify(body);
    }

    try {
        const response = await fetch(
            `${API_BASE_URL}/v${API_VERSION}${url}`,
            { method, headers: tokenHeaders, body: requestBody }
        );
        if (!response.ok) {
            throw new Error(
                `Status code: ${response.status}\nResponse: ${response.statusText}`
            );
        }
        if (parseJson) {
            return await response.json() as T;
        }
        return response;
    } catch (error) {
        console.error(`Error fetching ${url}:`, error);
        throw error;
    }
}
