import json
from typing import Any, Dict, Optional, Tuple
import requests


class ApiClient:
    """Client for interacting with the FastAPI backend REST API."""

    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip("/")
        self.token: Optional[str] = None
        self.current_user: Optional[Dict[str, Any]] = None
        self.timeout = 8.0  # seconds
        self.session = requests.Session()
        self.session.trust_env = False

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def check_health(self) -> Tuple[bool, str]:
        """Check if backend server is reachable."""
        try:
            res = self.session.get(f"{self.base_url}/health", timeout=3.0)
            if res.status_code == 200:
                return True, "Backend is healthy and reachable"
            return False, f"Backend returned status {res.status_code}"
        except requests.exceptions.ConnectionError:
            return False, "Cannot connect to backend server. Make sure FastAPI is running on http://127.0.0.1:8000"
        except Exception as e:
            return False, f"Connection error: {str(e)}"

    def register(
        self,
        full_name: str,
        email: str,
        password: str,
        confirm_password: str
    ) -> Tuple[bool, Any]:
        """Register a new user."""
        url = f"{self.base_url}/auth/register"
        payload = {
            "full_name": full_name,
            "email": email,
            "password": password,
            "confirm_password": confirm_password,
        }
        try:
            res = self.session.post(url, json=payload, headers=self._headers(), timeout=self.timeout)
            data = res.json()
            if res.status_code == 201:
                self.token = data.get("access_token")
                self.current_user = data.get("user")
                return True, data
            detail = data.get("detail", "Registration failed.")
            if isinstance(detail, list):
                detail = "; ".join([item.get("msg", str(item)) for item in detail])
            return False, str(detail)
        except requests.exceptions.ConnectionError:
            return False, "Server unavailable. Please verify FastAPI backend is running."
        except Exception as e:
            return False, f"Network error: {str(e)}"

    def login(self, email: str, password: str) -> Tuple[bool, Any]:
        """Log in an existing user."""
        url = f"{self.base_url}/auth/login"
        payload = {"email": email, "password": password}
        try:
            res = self.session.post(url, json=payload, headers=self._headers(), timeout=self.timeout)
            data = res.json()
            if res.status_code == 200:
                self.token = data.get("access_token")
                self.current_user = data.get("user")
                return True, data
            detail = data.get("detail", "Invalid email or password.")
            if isinstance(detail, list):
                detail = "; ".join([item.get("msg", str(item)) for item in detail])
            return False, str(detail)
        except requests.exceptions.ConnectionError:
            return False, "Server unavailable. Please verify FastAPI backend is running."
        except Exception as e:
            return False, f"Network error: {str(e)}"

    def get_profile(self) -> Tuple[bool, Any]:
        """Fetch current household profile."""
        url = f"{self.base_url}/profile"
        try:
            res = self.session.get(url, headers=self._headers(), timeout=self.timeout)
            data = res.json()
            if res.status_code == 200:
                return True, data
            return False, data.get("detail", "Profile not found")
        except Exception as e:
            return False, f"Network error: {str(e)}"

    def save_profile(
        self,
        household_members: int,
        house_type: str,
        location: str,
        num_bathrooms: int,
        people_usually_at_home: Optional[int] = None,
        unusual_occupancy: Optional[str] = "None"
    ) -> Tuple[bool, Any]:
        """Create or update household profile."""
        url = f"{self.base_url}/profile"
        payload = {
            "household_members": household_members,
            "house_type": house_type,
            "location": location,
            "num_bathrooms": num_bathrooms,
            "people_usually_at_home": people_usually_at_home,
            "unusual_occupancy": unusual_occupancy or "None"
        }
        try:
            res = self.session.post(url, json=payload, headers=self._headers(), timeout=self.timeout)
            data = res.json()
            if res.status_code in (200, 201):
                if self.current_user:
                    self.current_user["has_profile"] = True
                return True, data
            detail = data.get("detail", "Failed to save profile.")
            if isinstance(detail, list):
                detail = "; ".join([item.get("msg", str(item)) for item in detail])
            return False, str(detail)
        except requests.exceptions.ConnectionError:
            return False, "Server unavailable. Please check backend connection."
        except Exception as e:
            return False, f"Network error: {str(e)}"

    def save_electricity(
        self,
        monthly_consumption_kwh: float,
        ac_count: int = 0,
        fan_count: int = 0,
        refrigerator_count: int = 0,
        tv_count: int = 0,
        geyser_count: int = 0,
        washing_machine_count: int = 0,
        water_pump_count: int = 0,
        other_appliances: Optional[str] = None,
        usage_notes: Optional[str] = None
    ) -> Tuple[bool, Any]:
        """Save monthly electricity consumption record."""
        url = f"{self.base_url}/consumption/electricity"
        payload = {
            "monthly_consumption_kwh": monthly_consumption_kwh,
            "ac_count": ac_count,
            "fan_count": fan_count,
            "refrigerator_count": refrigerator_count,
            "tv_count": tv_count,
            "geyser_count": geyser_count,
            "washing_machine_count": washing_machine_count,
            "water_pump_count": water_pump_count,
            "other_appliances": other_appliances,
            "usage_notes": usage_notes
        }
        try:
            res = self.session.post(url, json=payload, headers=self._headers(), timeout=self.timeout)
            data = res.json()
            if res.status_code in (200, 201):
                return True, data
            detail = data.get("detail", "Failed to save electricity consumption.")
            if isinstance(detail, list):
                detail = "; ".join([item.get("msg", str(item)) for item in detail])
            return False, str(detail)
        except Exception as e:
            return False, f"Network error: {str(e)}"

    def save_water(
        self,
        monthly_consumption_litres: float,
        num_showers: int = 0,
        avg_shower_duration_mins: float = 0.0,
        bucket_usage: int = 0,
        washing_machine_usage: Optional[str] = None,
        garden_watering: Optional[str] = None,
        vehicle_washing: Optional[str] = None,
        water_pump_usage: Optional[str] = None,
        other_water_usage: Optional[str] = None
    ) -> Tuple[bool, Any]:
        """Save monthly water consumption record."""
        url = f"{self.base_url}/consumption/water"
        payload = {
            "monthly_consumption_litres": monthly_consumption_litres,
            "num_showers": num_showers,
            "avg_shower_duration_mins": avg_shower_duration_mins,
            "bucket_usage": bucket_usage,
            "washing_machine_usage": washing_machine_usage,
            "garden_watering": garden_watering,
            "vehicle_washing": vehicle_washing,
            "water_pump_usage": water_pump_usage,
            "other_water_usage": other_water_usage
        }
        try:
            res = self.session.post(url, json=payload, headers=self._headers(), timeout=self.timeout)
            data = res.json()
            if res.status_code in (200, 201):
                return True, data
            detail = data.get("detail", "Failed to save water consumption.")
            if isinstance(detail, list):
                detail = "; ".join([item.get("msg", str(item)) for item in detail])
            return False, str(detail)
        except Exception as e:
            return False, f"Network error: {str(e)}"

    def get_consumption_summary(self) -> Tuple[bool, Any]:
        """Fetch comprehensive consumption summary and analytics."""
        url = f"{self.base_url}/consumption/summary"
        try:
            res = self.session.get(url, headers=self._headers(), timeout=self.timeout)
            data = res.json()
            if res.status_code == 200:
                return True, data
            detail = data.get("detail", "Failed to fetch consumption summary.")
            if isinstance(detail, list):
                detail = "; ".join([item.get("msg", str(item)) for item in detail])
            return False, str(detail)
        except requests.exceptions.ConnectionError:
            return False, "Server unavailable. Please verify FastAPI backend is running."
        except Exception as e:
            return False, f"Network error: {str(e)}"

    def get_electricity_history(self) -> Tuple[bool, Any]:
        """Retrieve logged electricity consumption history."""
        url = f"{self.base_url}/consumption/electricity"
        try:
            res = self.session.get(url, headers=self._headers(), timeout=self.timeout)
            data = res.json()
            if res.status_code == 200:
                return True, data
            detail = data.get("detail", "Failed to fetch electricity history.")
            return False, str(detail)
        except Exception as e:
            return False, f"Network error: {str(e)}"

    def get_water_history(self) -> Tuple[bool, Any]:
        """Retrieve logged water consumption history."""
        url = f"{self.base_url}/consumption/water"
        try:
            res = self.session.get(url, headers=self._headers(), timeout=self.timeout)
            data = res.json()
            if res.status_code == 200:
                return True, data
            detail = data.get("detail", "Failed to fetch water history.")
            return False, str(detail)
        except Exception as e:
            return False, f"Network error: {str(e)}"

    def logout(self):
        """Clear token and active user session."""
        self.token = None
        self.current_user = None



# Shared singleton client instance
api_client = ApiClient()
