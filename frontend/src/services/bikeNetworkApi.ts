/**
 * API service for fetching bike network data
 */

export interface BikeNetworkRequest {
  city: string
}

export interface BikeNetworkResponse {
  type: string
  features: any[]
  [key: string]: any
}

const API_BASE_URL = 'https://bike-stress-model.onrender.com'
// const API_BASE_URL = 'https://corsproxy.io/?https://bike-stress-model.onrender.com'

/**
 * Fetch bike network GeoJSON data for a given city
 * @param city - City name in format "City, State, Country"
 * @returns Promise with GeoJSON data
 */
export async function fetchBikeNetwork(city: string): Promise<BikeNetworkResponse> {
  try {
    console.log('Making request to:', `${API_BASE_URL}/getNetwork`)
    console.log('Request body:', { city })

    const response = await fetch(`${API_BASE_URL}/getNetwork`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify({ city }),
    })

    console.log('Response status:', response.status)
    console.log('Response headers:', Object.fromEntries(response.headers.entries()))

    if (!response.ok) {
      const errorText = await response.text()
      console.error('Error response:', errorText)
      throw new Error(
        `API request failed: ${response.status} ${response.statusText}. ` +
          `This might be a CORS issue or the endpoint may not accept POST requests. ` +
          `Error: ${errorText}`,
      )
    }

    const data = await response.json()
    return data
  } catch (error) {
    if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
      throw new Error(
        'Network request failed. This is likely a CORS issue. ' +
          'The backend at bike-stress-model.onrender.com needs to enable CORS headers. ' +
          'Contact the API administrator to add Access-Control-Allow-Origin headers.',
      )
    }
    throw error
  }
}
