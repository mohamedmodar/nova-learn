import requests
import json

def test_with_new_user():
    """Register a new user and test recommendations"""
    
    base_url = "http://localhost:8000"
    
    print("=== Testing with New User ===")
    
    try:
        # 1. Register a new student
        print("1. Registering new student...")
        register_url = f"{base_url}/auth/register"
        student_data = {
            "full_name": "Test User",
            "email": "testuser@example.com",
            "password": "testpass123",
            "interests": ["Node.js", "React", "JavaScript"]
        }
        
        register_response = requests.post(register_url, json=student_data)
        if register_response.status_code == 200:
            print("✅ Student registered successfully")
            student = register_response.json()
            print(f"   Student ID: {student['id']}")
        elif register_response.status_code == 400 and "already registered" in register_response.text:
            print("✅ Student already exists, proceeding with login...")
        else:
            print(f"❌ Registration failed: {register_response.status_code}")
            print(f"Response: {register_response.text}")
            return
        
        # 2. Login
        print("\n2. Logging in...")
        login_url = f"{base_url}/auth/token"
        login_data = {
            "username": "testuser@example.com",
            "password": "testpass123"
        }
        
        login_response = requests.post(login_url, data=login_data)
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            print(f"Response: {login_response.text}")
            return
        
        token_data = login_response.json()
        token = token_data.get("access_token")
        print(f"✅ Login successful")
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # 3. Add some interactions to build a profile
        print("\n3. Adding some interactions...")
        interactions_url = f"{base_url}/interactions/"
        
        test_interactions = [
            {"course_id": "COURSE-791-AA", "interaction_type": "like"},  # Node.js course
            {"course_id": "COURSE-970-A", "interaction_type": "like"},   # Angular Node.js course
            {"course_id": "COURSE-998-AC", "interaction_type": "like"},  # Angular crash course
        ]
        
        for interaction in test_interactions:
            response = requests.post(interactions_url, json=interaction, headers=headers)
            if response.status_code == 200:
                print(f"   ✅ Added {interaction['interaction_type']} for {interaction['course_id']}")
            else:
                print(f"   ❌ Failed to add interaction: {response.status_code}")
        
        # 4. Test recommendations
        print("\n4. Fetching recommendations...")
        recommendations_url = f"{base_url}/recommendations/"
        
        payload = {"top_n": 6}
        
        rec_response = requests.post(recommendations_url, json=payload, headers=headers)
        print(f"Response status: {rec_response.status_code}")
        
        if rec_response.status_code == 200:
            recommendations = rec_response.json()
            print(f"✅ Got {len(recommendations)} recommendations")
            
            print("\n=== TOP RECOMMENDATIONS ===")
            for i, course in enumerate(recommendations[:5], 1):
                print(f"{i}. {course.get('title', 'Unknown Title')}")
                print(f"   ID: {course.get('item_id', course.get('id', 'Unknown ID'))}")
                if 'skills' in course:
                    skills = course['skills'][:3] if isinstance(course['skills'], list) else str(course['skills'])[:100]
                    print(f"   Skills: {skills}")
                print()
                
        else:
            print(f"❌ Recommendations failed: {rec_response.status_code}")
            print(f"Response: {rec_response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_with_new_user() 