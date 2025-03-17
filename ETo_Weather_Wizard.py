

"""
ETo approximation function
--------------
recollection of Weather data through APIs for ETo approximation

Reference:
Simplified forms for the standardized FAO-56 Penman–Monteith reference evapotranspiration using limited weather data
https://www.sciencedirect.com/science/article/abs/pii/S0022169413006501?via%3Dihub S
"""
import urequests
import json
import time
import ntptime
import math

#sync to utf - 5
def SyncTime():
    zzz = True
    while zzz == True:
     try:
        ntptime.settime()
        print("Synced to NTP")
        clock = time.localtime(time.time() - 5 * 3600)
        zzz = False 

     except Exception as e:
        print("ERROR", e)
        clock = time.localtime(time.time() - 5 * 3600)
    return clock
clock = SyncTime()


date = (str(clock[0])+"/"+str(clock[1])+"/" +str(clock[2])+" - "+str(clock[3])+":"+str(clock[4])+":"+str(clock[5]))



def ETo(Rs, T, Tmax, Tmin, RH, u):





    ALPHA = 0.23
    PHI =0.1491


    i = 7
    J = int(30.5 * i - 14.6)
    angle = ((2 * math.pi * J) / (365)) - 1.39
    DELTA = 0.409 * math.sin(angle)

    N = PHI*DELTA*9.8+12

    C1 = 3.9
    C2 = 0.15
    C3 = 0.16

    K = C1*(Rs/(N**2))*(PHI**C2)+C3

    TR = Tmax - Tmin
    Z = 400


    P1 = (0.051*(1 - ALPHA)*(Rs)*(math.sqrt(T+9.5)))


    P2 = 0.188*(T+13)*(K-0.194)*(1-0.00015*((T+45)**2)*math.sqrt(RH/100))

    P3 =(0.0165*Rs*(u**0.7))

    P4 = 0.0585*(T+17)*(u**0.75)*((((1+0.00043*(TR**2))**2) -(RH/100))/((1+0.00043*(TR**2))**2))

    P5 = 0.0001*Z

  


    ANS = P1 - P2 -P3 + P4 + P5

    return ANS
#mqtt
from MQTT import *



# Function to fetch data and update JSON
def fetch_and_update():
    
    # API keys and URLs
    WBcurrent_backup = ''
    WBcurrent_weather_url = ''
    
    WBforecast_backup = ''
    WBforecast_url = ''
    
    OWMcurrent_weather_url = ''
    OWMforecast_url =''
    
    global T
    global Tmax
    global Tmin
    global Rs
    global RH
    global u
    global pop
    
    # Fetch current weather data
    try:
      try:
       WBcurrent_response = urequests.get(WBcurrent_weather_url)
       WBcurrent_data = WBcurrent_response.json()['data'][0]
      except Exception as e:
       print("ERROR:WBcurrent_weather_url", e)
       time.sleep(72)
       WBcurrent_response = urequests.get(WBcurrent_backup)
       WBcurrent_data = WBcurrent_response.json()['data'][0]
       
       
      
      T = WBcurrent_data['temp']
      Rs = WBcurrent_data['solar_rad']
      Rs = Rs/11.57
      RH = WBcurrent_data['rh']
      u = WBcurrent_data['wind_spd']
      
      
      
      # Save current data to JSON file
      try:
       with open('current_Weatherbit.json', 'w') as WBcurrent_file:
        json.dump(WBcurrent_data, WBcurrent_file)
       WBcurrent_response.close()
       print("current_Weatherbit.json saved")
      except Exception as e:
       print("ERROR", e)
    
    except Exception as e:
     print("ERROR: Current_backup", e)
     OWMcurrent_response = urequests.get(OWMcurrent_weather_url)
     OWMcurrent_data = OWMcurrent_response.json()
     T = OWMcurrent_data['main']['temp']
     Rs = 0
     RH = OWMcurrent_data['main']['humidity']
     u = OWMcurrent_data['wind']['speed']
      
      # Save current data to JSON file
     with open('current_OpenWeatherMap.json', 'w') as OWMcurrent_file:
      json.dump(OWMcurrent_data, OWMcurrent_file)
     OWMcurrent_response.close()
     print("current_OpenWeatherMap.json saved")
        
    # Fetch forecast data
    try:
     try:
       WBforecast_response = urequests.get(WBforecast_url)
       WBforecast_data = WBforecast_response.json()['data'][0]
       Tmax = WBforecast_data['max_temp']
     except Exception as e:
       print("ERROR: WBforecast_url", e)
       WBforecast_response = urequests.get(WBforecast_backup)
       WBforecast_data = WBforecast_response.json()['data'][0]
       
        
     
     Tmax = WBforecast_data['max_temp']
     Tmin = WBforecast_data['min_temp']
     pop =  WBforecast_data['pop']
       
     with open('forecast_Weatherbit.json', 'w') as WBforecast_file:
      json.dump(WBforecast_data,WBforecast_file)
     WBforecast_response.close()
     print("forecast_Weatherbit.json saved")
     
    except Exception as e:
     print("ERROR: WBforecast_backup", e)
     OWMcurrent_response = urequests.get(OWMcurrent_weather_url)
     OWMcurrent_data = OWMcurrent_response.json()
     Tmax = OWMcurrent_data['main']['temp_max']
     Tmin = OWMcurrent_data['main']['temp_min']
     pop = False
        
     OWMcurrent_response.close() 
    
    
    
    # Calculate ETo
    global eto
    eto = ETo(Rs, T, Tmax, Tmin, RH, u)
    print(eto)
    
    
    date = (str(clock[0])+"/"+str(clock[1])+"/" +str(clock[2])+" - "+str(clock[3])+":"+str(clock[4])+":"+str(clock[5]))
    
     # Prepare data for JSON output
    weather_data = {
        "date": date,
        "ETo": eto,
        "T(C)": T,
        "Tmax(C)": Tmax,
        "Tmin(C)": Tmin,
        "RH(%)": RH,
        "u(m/s)": u,
        "Rs(MJ/m^2/d)": Rs,
        "pop" : pop
    }
    
    
    
    
    try: 
       if pop >= 80:
           with open('rain.json', 'w') as weather_file:
               handle = {"Rain":True}
               json.dump(handle, weather_file)
               print(" Rain status saved")
        
    except Exception as e:
        print("ERROR: no POP value", e)

    
    
    with open('Max_ETo.json', 'r') as file:
        data = file.read()
        hand = json.loads(data)
        RealMaxETo = hand["ETo"]
        if eto > RealMaxETo:
            with open('Max_ETo.json', 'w') as weather_file:
                Max_ETo = {"ETo":eto}
                json.dump(Max_ETo, weather_file)
                print(" max ETo data saved")
            

    # Save the data to a JSON file
    with open('data.json', 'w') as weather_file:
        json.dump(weather_data, weather_file)
        print(" data saved")
   
    with open('data.json', 'r') as weather_file:
        data = weather_file.read()
        client = ConnectMQTT()
        Publish("Weather_Data",str(data))
        DisconnectMQTT(client)
        print(data)
        
