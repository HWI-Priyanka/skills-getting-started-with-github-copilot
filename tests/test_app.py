"""
Comprehensive test suite for the Mergington High School API

Tests cover all endpoints: GET /activities, POST /activities/{activity_name}/signup,
and DELETE /activities/{activity_name}/participants/{email}

All tests follow the AAA (Arrange-Act-Assert) pattern.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a TestClient instance for testing the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to initial state before each test to ensure test independence"""
    initial_activities = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        },
        "Basketball Team": {
            "description": "Competitive basketball team for interscholastic games",
            "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
            "max_participants": 15,
            "participants": ["james@mergington.edu"]
        },
        "Tennis Club": {
            "description": "Learn tennis skills and participate in friendly matches",
            "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:00 PM",
            "max_participants": 16,
            "participants": ["alex@mergington.edu", "ryan@mergington.edu"]
        },
        "Art Club": {
            "description": "Explore various art techniques including painting, drawing, and sculpture",
            "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
            "max_participants": 18,
            "participants": ["maya@mergington.edu"]
        },
        "Music Ensemble": {
            "description": "Join our instrumental and vocal ensemble for performances",
            "schedule": "Mondays and Fridays, 4:30 PM - 5:30 PM",
            "max_participants": 25,
            "participants": ["lily@mergington.edu", "noah@mergington.edu"]
        },
        "Debate Club": {
            "description": "Develop argumentation and public speaking skills through competitive debate",
            "schedule": "Thursdays, 3:30 PM - 5:00 PM",
            "max_participants": 14,
            "participants": ["lucas@mergington.edu"]
        },
        "Math Olympiad": {
            "description": "Solve challenging math problems and compete in mathematical competitions",
            "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
            "max_participants": 12,
            "participants": ["ava@mergington.edu", "ethan@mergington.edu"]
        }
    }
    
    # Clear existing activities
    activities.clear()
    
    # Restore initial state
    for activity_name, activity_data in initial_activities.items():
        activities[activity_name] = {
            "description": activity_data["description"],
            "schedule": activity_data["schedule"],
            "max_participants": activity_data["max_participants"],
            "participants": activity_data["participants"].copy()
        }
    
    yield
    
    # Cleanup after test (optional, but good practice)
    activities.clear()


# ============================================================================
# GET /activities Endpoint Tests
# ============================================================================

def test_get_activities_returns_all_activities(client):
    """Happy path: Verify GET /activities returns all activities"""
    # Arrange
    expected_activity_names = {
        "Chess Club", "Programming Class", "Gym Class", "Basketball Team",
        "Tennis Club", "Art Club", "Music Ensemble", "Debate Club", "Math Olympiad"
    }
    
    # Act
    response = client.get("/activities")
    
    # Assert
    assert response.status_code == 200
    activities_data = response.json()
    assert set(activities_data.keys()) == expected_activity_names
    assert len(activities_data) == 9


def test_get_activities_response_structure(client):
    """Verify each activity has required fields: description, schedule, max_participants, participants"""
    # Arrange
    required_fields = {"description", "schedule", "max_participants", "participants"}
    
    # Act
    response = client.get("/activities")
    
    # Assert
    assert response.status_code == 200
    activities_data = response.json()
    
    # Verify each activity has all required fields
    for activity_name, activity_data in activities_data.items():
        assert set(activity_data.keys()) == required_fields, \
            f"Activity '{activity_name}' is missing required fields"
        assert isinstance(activity_data["description"], str)
        assert isinstance(activity_data["schedule"], str)
        assert isinstance(activity_data["max_participants"], int)
        assert isinstance(activity_data["participants"], list)
        assert all(isinstance(p, str) for p in activity_data["participants"]), \
            f"Activity '{activity_name}' has non-string participants"


# ============================================================================
# POST /activities/{activity_name}/signup Endpoint Tests
# ============================================================================

def test_signup_new_participant_success(client):
    """Happy path: Successfully sign up a new participant to an activity"""
    # Arrange
    activity_name = "Chess Club"
    new_email = "newstudent@mergington.edu"
    participants_before = len(activities[activity_name]["participants"])
    
    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": new_email}
    )
    
    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {new_email} for {activity_name}"}
    assert new_email in activities[activity_name]["participants"]
    assert len(activities[activity_name]["participants"]) == participants_before + 1


def test_signup_activity_not_found(client):
    """Error case: Return 404 when trying to sign up for non-existent activity"""
    # Arrange
    nonexistent_activity = "Nonexistent Club"
    test_email = "student@mergington.edu"
    
    # Act
    response = client.post(
        f"/activities/{nonexistent_activity}/signup",
        params={"email": test_email}
    )
    
    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_duplicate_registration(client):
    """Error case: Return 400 when student is already registered for the activity"""
    # Arrange
    activity_name = "Chess Club"
    already_registered_email = "michael@mergington.edu"  # Already in participants
    
    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": already_registered_email}
    )
    
    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Student already signed up for this activity"}


def test_signup_capacity_exceeded(client):
    """Edge case: Successfully add participant up to max capacity"""
    # Arrange
    activity_name = "Math Olympiad"
    current_participants = activities[activity_name]["participants"].copy()
    max_participants = activities[activity_name]["max_participants"]
    
    # Fill the activity to capacity
    assert len(current_participants) < max_participants, \
        "Setup error: Activity should not be at capacity"
    
    # Calculate how many more participants we can add
    new_emails = [f"student{i}@mergington.edu" for i in range(max_participants - len(current_participants))]
    
    # Act: Sign up participants up to capacity
    responses = []
    for email in new_emails:
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        responses.append(response)
    
    # Assert: All signups should succeed up to capacity
    for response in responses:
        assert response.status_code == 200
    
    # Verify activity is now at capacity
    assert len(activities[activity_name]["participants"]) == max_participants
    
    # Attempt to add one more participant (would exceed capacity)
    overfull_email = "overfull@mergington.edu"
    response_overfull = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": overfull_email}
    )
    
    # The endpoint doesn't prevent capacity overflow, so this will succeed
    # This tests the current behavior but documents that capacity is not enforced
    assert response_overfull.status_code == 200
    assert overfull_email in activities[activity_name]["participants"]


# ============================================================================
# DELETE /activities/{activity_name}/participants/{email} Endpoint Tests
# ============================================================================

def test_delete_participant_success(client):
    """Happy path: Successfully remove an existing participant from an activity"""
    # Arrange
    activity_name = "Chess Club"
    email_to_remove = "michael@mergington.edu"
    participants_before = len(activities[activity_name]["participants"])
    
    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants/{email_to_remove}"
    )
    
    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email_to_remove} from {activity_name}"}
    assert email_to_remove not in activities[activity_name]["participants"]
    assert len(activities[activity_name]["participants"]) == participants_before - 1


def test_delete_participant_not_found(client):
    """Error case: Return 404 when trying to remove participant from non-existent activity"""
    # Arrange
    nonexistent_activity = "Nonexistent Club"
    test_email = "student@mergington.edu"
    
    # Act
    response = client.delete(
        f"/activities/{nonexistent_activity}/participants/{test_email}"
    )
    
    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_delete_participant_not_registered(client):
    """Error case: Return 400 when trying to remove participant not signed up for activity"""
    # Arrange
    activity_name = "Programming Class"
    unregistered_email = "notregistered@mergington.edu"
    
    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants/{unregistered_email}"
    )
    
    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Student not signed up for this activity"}


def test_delete_participant_actually_removed(client):
    """Verify participant is completely removed from the activity's participants list"""
    # Arrange
    activity_name = "Tennis Club"
    email_to_remove = "alex@mergington.edu"
    
    # Verify participant exists before deletion
    assert email_to_remove in activities[activity_name]["participants"]
    participants_before = activities[activity_name]["participants"].copy()
    
    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants/{email_to_remove}"
    )
    
    # Assert
    assert response.status_code == 200
    
    # Verify participant is not in the list anymore
    assert email_to_remove not in activities[activity_name]["participants"]
    
    # Verify the list size decreased by exactly 1
    assert len(activities[activity_name]["participants"]) == len(participants_before) - 1
    
    # Verify no other participants were affected
    expected_remaining = [p for p in participants_before if p != email_to_remove]
    assert activities[activity_name]["participants"] == expected_remaining
