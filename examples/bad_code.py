
import sys
import os
import json
import time

# Globalne zmienne (naruszenie)
GLOBAL_DATA = {}
USER_CACHE = []

def process_user_data(username, email, phone, address, age, status, preferences, history, notes, metadata):
    # Funkcja z zbyt wieloma parametrami (10 > 5)
    # Brak docstring (naruszenie)
    
    print(f"Processing user: {username}")  # Print statement (naruszenie)
    
    global GLOBAL_DATA  # Użycie global (naruszenie)
    
    # Wysoka złożoność cyklomatyczna (naruszenie)
    if age > 18:
        if status == "active":
            if len(preferences) > 0:
                if email.endswith("@gmail.com"):
                    if phone.startswith("+"):
                        if len(address) > 10:
                            if "premium" in history:
                                if len(notes) > 0:
                                    if metadata and "verified" in metadata:
                                        result = "premium_verified_user"
                                    else:
                                        result = "premium_unverified_user"
                                else:
                                    result = "premium_no_notes"
                            else:
                                result = "regular_user"
                        else:
                            result = "invalid_address"
                    else:
                        result = "invalid_phone"
                else:
                    result = "non_gmail_user"
            else:
                result = "no_preferences"
        else:
            result = "inactive_user"
    else:
        result = "minor_user"
    
    GLOBAL_DATA[username] = result
    USER_CACHE.append(username)
    
    # Długa funkcja - ponad 50 linii
    time.sleep(0.1)
    print(f"Processed: {result}")
    
    return result

def another_long_function():
    # Kolejna funkcja bez docstring
    data = []
    for i in range(100):
        for j in range(50):
            if i % 2 == 0:
                if j % 3 == 0:
                    if i + j > 10:
                        if i * j < 1000:
                            data.append(i + j)
                        else:
                            data.append(i - j)
                    else:
                        data.append(i * j)
                else:
                    data.append(i // 2)
            else:
                data.append(j)
    
    print(f"Generated {len(data)} items")
    return data

# Funkcja z nieprawidłową konwencją nazewnictwa
def processDataAndReturnResults(inputData, ConfigurationOptions, UserPreferences):
    # CamelCase zamiast snake_case (naruszenie)
    # Parametry też w CamelCase
    
    Results = []  # Zmienna w CamelCase
    
    for Item in inputData:
        print(Item)  # Print statement
        Results.append(Item.upper())
    
    return Results

class ExampleClass:
    # Klasa bez docstring
    
    def __init__(self, param1, param2, param3, param4, param5, param6):
        # Zbyt wiele parametrów w konstruktorze
        self.param1 = param1
        self.param2 = param2
        self.param3 = param3
        self.param4 = param4
        self.param5 = param5
        self.param6 = param6
    
    def complex_method(self):
        # Metoda bez docstring i wysoka złożoność
        result = 0
        for i in range(100):
            if i % 2 == 0:
                if i % 4 == 0:
                    if i % 8 == 0:
                        if i % 16 == 0:
                            result += i * 2
                        else:
                            result += i
                    else:
                        result -= i
                else:
                    result += i // 2
            else:
                result += 1
        
        print(f"Complex result: {result}")
        return result

# Więcej kodu aby przekroczyć limit 300 linii pliku...
def dummy_function_1():
    print("Dummy 1")
    pass

def dummy_function_2():
    print("Dummy 2")
    pass

# ... (więcej funkcji dummy aby osiągnąć > 300 linii)
