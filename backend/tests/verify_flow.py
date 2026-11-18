"""
End-to-End flow verification script.
Tests the full Phase 1 flow using the mobile ApiClient against the live FastAPI server.
"""

import sys
import time
import os

# Ensure KIVY_HOME for Windows sandbox safety
if "KIVY_HOME" not in os.environ:
    os.environ["KIVY_HOME"] = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".kivy"))

# Ensure paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "mobile")))

from services.api_client import ApiClient

def main():
    client = ApiClient(base_url="http://127.0.0.1:8000")
    print("=== STEP 1: Checking Backend Health ===")
    healthy, msg = client.check_health()
    print(f"Health check: {healthy} | {msg}")
    assert healthy, "Backend must be healthy"

    timestamp = int(time.time() * 1000)
    test_email = f"resident_{timestamp}@greenliving.org"
    password = "SafePassword99!"
    full_name = f"Aarav Mehta {timestamp}"

    print("\n=== STEP 2: Testing User Registration ===")
    ok, res = client.register(
        full_name=full_name,
        email=test_email,
        password=password,
        confirm_password=password
    )
    print(f"Registration status: {ok}")
    assert ok, f"Registration failed: {res}"
    print(f"Registered User ID: {res['user']['id']}, Token length: {len(res['access_token'])}")

    print("\n=== STEP 3: Testing Duplicate Registration Prevention ===")
    dup_ok, dup_res = client.register(
        full_name=full_name,
        email=test_email,
        password=password,
        confirm_password=password
    )
    print(f"Duplicate rejected as expected: {not dup_ok} | Detail: {dup_res}")
    assert not dup_ok, "Duplicate email registration should fail"

    print("\n=== STEP 4: Testing Authentication / Login ===")
    # Bad credentials
    bad_ok, bad_res = client.login(test_email, "WrongPassword!")
    print(f"Bad login rejected as expected: {not bad_ok} | Detail: {bad_res}")
    assert not bad_ok, "Bad password should fail"

    # Good credentials
    login_ok, login_res = client.login(test_email, password)
    print(f"Good login succeeded: {login_ok}")
    assert login_ok, "Valid login should succeed"

    print("\n=== STEP 5: Testing Household Profile Submission ===")
    prof_ok, prof_res = client.save_profile(
        household_members=4,
        house_type="Apartment",
        location="Indirapuram, NCR",
        num_bathrooms=2,
        people_usually_at_home=2,
        unusual_occupancy="None"
    )
    print(f"Profile creation status: {prof_ok}")
    assert prof_ok, f"Profile save failed: {prof_res}"
    print(f"Profile ID: {prof_res['id']}, Members: {prof_res['household_members']}")

    # Verify profile get
    get_p_ok, get_p_res = client.get_profile()
    assert get_p_ok and get_p_res["location"] == "Indirapuram, NCR"
    print(f"Profile GET verified successfully.")

    print("\n=== STEP 6: Testing Electricity Consumption Submission ===")
    elec_ok, elec_res = client.save_electricity(
        monthly_consumption_kwh=310.5,
        ac_count=2,
        fan_count=4,
        refrigerator_count=1,
        tv_count=1,
        geyser_count=1,
        washing_machine_count=1,
        water_pump_count=1,
        other_appliances="Microwave, Router",
        usage_notes="AC running 6 hrs/night in master bedroom"
    )
    print(f"Electricity submission status: {elec_ok}")
    assert elec_ok, f"Electricity save failed: {elec_res}"
    print(f"Electricity record ID: {elec_res['id']}, kWh: {elec_res['monthly_consumption_kwh']}")

    print("\n=== STEP 7: Testing Water Consumption Submission ===")
    water_ok, water_res = client.save_water(
        monthly_consumption_litres=13500.0,
        num_showers=4,
        avg_shower_duration_mins=7.5,
        bucket_usage=2,
        washing_machine_usage="3 loads/week",
        garden_watering="Daily potted plants",
        vehicle_washing="Weekly car wash",
        water_pump_usage="40 mins/day",
        other_water_usage="Balcony cleanup"
    )
    print(f"Water submission status: {water_ok}")
    assert water_ok, f"Water save failed: {water_res}"
    print(f"Water record ID: {water_res['id']}, Litres: {water_res['monthly_consumption_litres']}")

    print("\n=== STEP 8: Testing Consumption Summary & Analytics via ApiClient ===")
    sum_ok, sum_res = client.get_consumption_summary()
    print(f"Summary fetch status: {sum_ok}")
    assert sum_ok, f"Summary fetch failed: {sum_res}"
    assert sum_res["has_profile"] is True
    assert sum_res["electricity"]["latest_record"]["monthly_consumption_kwh"] == 310.5
    assert sum_res["electricity"]["per_person_kwh"] == round(310.5 / 4, 2)
    assert sum_res["water"]["latest_record"]["monthly_consumption_litres"] == 13500.0
    assert sum_res["water"]["per_person_litres_monthly"] == round(13500.0 / 4, 2)
    assert sum_res["water"]["per_person_litres_daily"] == round(13500.0 / (4 * 30), 2)
    print(f"Summary verified: Per-person kWh: {sum_res['electricity']['per_person_kwh']}, Daily LPCD: {sum_res['water']['per_person_litres_daily']}")

    print("\n==========================================")
    print("ALL MVP & PHASE 2 FLOW CHECKS PASSED 100%!")
    print("==========================================")

if __name__ == "__main__":
    main()
