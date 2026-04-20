import requests
from core import config
from core import state_manager
from core import location_helper

def handle(command, speak):
    if "weather" not in command and "temperature" not in command and "rain" not in command:
        return False

    # PROACTIVE: Always sync location first to ensure the forecast is accurate
    location_helper.sync_location()
    
    city = state_manager.current_city
    coords = {"lat": state_manager.current_lat, "lon": state_manager.current_lon}
    
    speak(f"Checking the local environmental data for {city}...")
    
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={coords['lat']}&longitude={coords['lon']}&current_weather=True&daily=precipitation_probability_max&timezone=auto"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            current = data["current_weather"]
            temp = current["temperature"]
            wind = current["windspeed"]
            
            # Get rain probability for today
            rain_prob = data["daily"]["precipitation_probability_max"][0]
            
            report = f"The current temperature in {city} is {int(temp)} degrees Celsius. "
            if rain_prob > 30:
                report += f"There is a {rain_prob} percent chance of rain today, so you might want an umbrella."
            else:
                report += "The skies look relatively clear for now."
            
            speak(report)
            state_manager.add_to_chat("SEVEN", f"--- WEATHER REPORT: {city} ---\nTemp: {temp}°C\nWind: {wind} km/h\nRain Prob: {rain_prob}%")
            return True
        else:
            speak("I'm sorry, I'm having trouble reaching the meteorological servers right now.")
    except Exception as e:
        print(f"[Weather Error] {e}")
        speak("I encountered an error while analyzing the weather data.")
    
    return True
