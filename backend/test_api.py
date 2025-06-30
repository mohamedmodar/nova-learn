import requests
import json

def test_recommendations_api():
    """Test the recommendations API directly"""
    
    # First, let's try to login to get a token
    login_url = "http://localhost:8000/auth/token"
    login_data = {
        "username": "mosatafa@gmail.com",  # The user with Node.js likes
        "password": "123456"
    }
    
    print("=== Testing Recommendations API ===")
    
    try:
        # Login using form data (OAuth2PasswordRequestForm)
        print("1. Logging in...")
        login_response = requests.post(login_url, data=login_data)
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            print(f"Response: {login_response.text}")
            return
        
        token_data = login_response.json()
        token = token_data.get("access_token")
        print(f"✅ Login successful, got token")
        
        # Get recommendations
        print("\n2. Fetching recommendations...")
        recommendations_url = "http://localhost:8000/recommendations/"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
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
    test_recommendations_api() 