"""
Tests for the High School Management System API
"""

import sys
from pathlib import Path

# Add src directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_dict(self):
        """Test that get_activities returns a dictionary"""
        response = client.get("/activities")
        assert response.status_code == 200
        assert isinstance(response.json(), dict)

    def test_get_activities_contains_expected_activities(self):
        """Test that get_activities returns expected activities"""
        response = client.get("/activities")
        activities = response.json()
        assert "Chess Club" in activities
        assert "Programming Class" in activities
        assert "Gym Class" in activities

    def test_activity_has_required_fields(self):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        activities = response.json()
        activity = activities["Chess Club"]
        
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_new_participant_success(self):
        """Test successfully signing up a new participant"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]

    def test_signup_duplicate_participant_fails(self):
        """Test that signing up the same participant twice fails"""
        email = "duplicate@mergington.edu"
        
        # First signup should succeed
        response1 = client.post(
            f"/activities/Chess%20Club/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Second signup should fail
        response2 = client.post(
            f"/activities/Chess%20Club/signup?email={email}"
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]

    def test_signup_nonexistent_activity_fails(self):
        """Test that signing up for a nonexistent activity fails"""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_returns_confirmation_message(self):
        """Test that signup returns proper confirmation message"""
        email = "testuser@mergington.edu"
        response = client.post(
            f"/activities/Chess%20Club/signup?email={email}"
        )
        result = response.json()
        assert email in result["message"]
        assert "Chess Club" in result["message"]


class TestUnregister:
    """Tests for POST /activities/{activity_name}/unregister endpoint"""

    def test_unregister_existing_participant_success(self):
        """Test successfully unregistering an existing participant"""
        # First signup
        email = "unregister_test@mergington.edu"
        client.post(f"/activities/Drama%20Club/signup?email={email}")
        
        # Then unregister
        response = client.post(
            f"/activities/Drama%20Club/unregister?email={email}"
        )
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]

    def test_unregister_nonexistent_participant_fails(self):
        """Test that unregistering a non-registered participant fails"""
        response = client.post(
            "/activities/Chess%20Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]

    def test_unregister_nonexistent_activity_fails(self):
        """Test that unregistering from a nonexistent activity fails"""
        response = client.post(
            "/activities/Nonexistent%20Activity/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_returns_confirmation_message(self):
        """Test that unregister returns proper confirmation message"""
        email = "unregister_confirm@mergington.edu"
        # First signup
        client.post(f"/activities/Art%20Studio/signup?email={email}")
        
        # Then unregister
        response = client.post(
            f"/activities/Art%20Studio/unregister?email={email}"
        )
        result = response.json()
        assert email in result["message"]
        assert "Art Studio" in result["message"]


class TestDuplicateRegistrationBug:
    """Tests for the duplicate registration bug fix"""

    def test_duplicate_registration_prevented(self):
        """Test that the duplicate registration bug is fixed"""
        email = "duplicate_bug_test@mergington.edu"
        activity = "Programming%20Class"
        
        # First registration should succeed
        response1 = client.post(f"/activities/{activity}/signup?email={email}")
        assert response1.status_code == 200
        
        # Verify participant count after first signup
        activities_before = client.get("/activities").json()
        count_before = len(activities_before["Programming Class"]["participants"])
        
        # Second registration should fail
        response2 = client.post(f"/activities/{activity}/signup?email={email}")
        assert response2.status_code == 400
        
        # Verify participant count hasn't increased
        activities_after = client.get("/activities").json()
        count_after = len(activities_after["Programming Class"]["participants"])
        
        assert count_before == count_after, "Participant count should not increase after failed duplicate registration"
