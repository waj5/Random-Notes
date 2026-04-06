/** Open-Meteo current weather WMO code; no API key. */
export async function fetchCurrentWeatherWmoCode(): Promise<number | null> {
  return new Promise((resolve) => {
    if (!navigator.geolocation) {
      resolve(null)
      return
    }
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        try {
          const lat = pos.coords.latitude
          const lon = pos.coords.longitude
          const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current_weather=true`
          const res = await fetch(url)
          if (!res.ok) {
            resolve(null)
            return
          }
          const data = await res.json()
          const code = data?.current_weather?.weathercode
          resolve(typeof code === 'number' ? code : null)
        } catch {
          resolve(null)
        }
      },
      () => resolve(null),
      { enableHighAccuracy: false, timeout: 12_000, maximumAge: 300_000 },
    )
  })
}
