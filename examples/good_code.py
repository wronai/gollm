# examples/good_code.py
"""
Przykład dobrego kodu zgodnego ze standardami goLLM.

Ten moduł demonstruje właściwe praktyki kodowania w Python.
"""

import logging
from dataclasses import dataclass
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)

@dataclass
class UserData:
    """Struktura danych użytkownika."""
    username: str
    email: str
    phone: str
    address: str
    age: int

@dataclass
class UserPreferences:
    """Preferencje użytkownika."""
    status: str
    preferences: List[str]
    history: List[str]
    notes: str
    metadata: Optional[Dict[str, Any]] = None

class UserProcessor:
    """Przetwarza dane użytkowników zgodnie z regułami biznesowymi."""
    
    def __init__(self):
        """Inicjalizuje procesor użytkowników."""
        self.processed_users: Dict[str, str] = {}
        self.user_cache: List[str] = []
    
    def process_user(self, user_data: UserData, preferences: UserPreferences) -> str:
        """
        Przetwarza dane użytkownika i zwraca jego kategorię.
        
        Args:
            user_data: Podstawowe dane użytkownika
            preferences: Preferencje i historia użytkownika
            
        Returns:
            str: Kategoria użytkownika
        """
        logger.info(f"Processing user: {user_data.username}")
        
        # Walidacja wieku
        if not self._is_adult(user_data.age):
            return "minor_user"
        
        # Sprawdź status aktywności
        if not self._is_active_user(preferences.status):
            return "inactive_user"
        
        # Określ kategorię na podstawie preferencji
        category = self._determine_user_category(user_data, preferences)
        
        # Zapisz wynik
        self._save_processing_result(user_data.username, category)
        
        logger.info(f"User {user_data.username} categorized as: {category}")
        return category
    
    def _is_adult(self, age: int) -> bool:
        """Sprawdza czy użytkownik jest pełnoletni."""
        return age >= 18
    
    def _is_active_user(self, status: str) -> bool:
        """Sprawdza czy użytkownik jest aktywny."""
        return status == "active"
    
    def _determine_user_category(self, user_data: UserData, preferences: UserPreferences) -> str:
        """
        Określa kategorię użytkownika na podstawie danych.
        
        Args:
            user_data: Dane użytkownika
            preferences: Preferencje użytkownika
            
        Returns:
            str: Kategoria użytkownika
        """
        # Sprawdź czy użytkownik premium
        if self._is_premium_user(preferences.history):
            return self._get_premium_category(user_data, preferences)
        
        # Sprawdź standardowe kryteria
        if self._has_valid_contact_data(user_data):
            return "verified_user"
        
        return "regular_user"
    
    def _is_premium_user(self, history: List[str]) -> bool:
        """Sprawdza czy użytkownik ma status premium."""
        return "premium" in history
    
    def _get_premium_category(self, user_data: UserData, preferences: UserPreferences) -> str:
        """Określa kategorię użytkownika premium."""
        if self._is_verified_user(preferences.metadata):
            return "premium_verified_user"
        return "premium_unverified_user"
    
    def _is_verified_user(self, metadata: Optional[Dict[str, Any]]) -> bool:
        """Sprawdza czy użytkownik jest zweryfikowany."""
        return metadata is not None and metadata.get("verified", False)
    
    def _has_valid_contact_data(self, user_data: UserData) -> bool:
        """Sprawdza poprawność danych kontaktowych."""
        return (
            self._is_valid_email(user_data.email) and
            self._is_valid_phone(user_data.phone) and
            self._is_valid_address(user_data.address)
        )
    
    def _is_valid_email(self, email: str) -> bool:
        """Sprawdza poprawność adresu email."""
        return email.endswith("@gmail.com")
    
    def _is_valid_phone(self, phone: str) -> bool:
        """Sprawdza poprawność numeru telefonu."""
        return phone.startswith("+")
    
    def _is_valid_address(self, address: str) -> bool:
        """Sprawdza poprawność adresu."""
        return len(address) > 10
    
    def _save_processing_result(self, username: str, category: str) -> None:
        """Zapisuje wynik przetwarzania."""
        self.processed_users[username] = category
        self.user_cache.append(username)

def process_data_list(input_data: List[str]) -> List[str]:
    """
    Przetwarza listę danych wejściowych.
    
    Args:
        input_data: Lista ciągów do przetworzenia
        
    Returns:
        List[str]: Przetworzone dane
    """
    logger.info(f"Processing {len(input_data)} items")
    
    results = []
    for item in input_data:
        processed_item = item.upper()
        results.append(processed_item)
    
    logger.info(f"Processed {len(results)} items successfully")
    return results
