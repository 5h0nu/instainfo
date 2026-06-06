import requests
import random
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# List of modern desktop user agents to rotate and simulate real browser requests
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0"
]

def get_instagram_profile(username: str, proxy: str = None) -> dict:
    """
    Fetches Instagram profile details using the internal web_profile_info API.
    
    :param username: The Instagram username to fetch
    :param proxy: Optional proxy URL (e.g., 'http://user:pass@host:port')
    :return: Dictionary containing profile information or error details
    """
    # Clean the username
    username = username.strip().lower()
    if username.startswith('@'):
        username = username[1:]
        
    if not username:
        return {
            "success": False,
            "error": "Username cannot be empty",
            "status_code": 400
        }
        
    url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
    
    # Select a random user agent
    user_agent = random.choice(USER_AGENTS)
    
    # Instagram requires these headers, especially x-ig-app-id and Referer
    headers = {
        "User-Agent": user_agent,
        "x-ig-app-id": "936619743392459",
        "Referer": f"https://www.instagram.com/{username}/",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "X-Requested-With": "XMLHttpRequest"
    }
    
    # Configure proxies if provided
    proxies = None
    if proxy:
        proxies = {
            "http": proxy,
            "https": proxy
        }
        logger.info(f"Using proxy: {proxy}")
        
    try:
        logger.info(f"Fetching Instagram profile info for: {username}")
        response = requests.get(url, headers=headers, proxies=proxies, timeout=15)
        
        if response.status_code == 200:
            try:
                data = response.json()
                user_data = data.get('data', {}).get('user')
                
                if not user_data:
                    logger.warning(f"Response success but user data missing for {username}")
                    return {
                        "success": False,
                        "error": "Instagram returned empty profile data",
                        "status_code": 404
                    }
                
                # Extract details
                profile_info = {
                    "success": True,
                    "username": user_data.get("username"),
                    "name": user_data.get("full_name"),
                    "followers_count": user_data.get("edge_followed_by", {}).get("count", 0),
                    "following_count": user_data.get("edge_follow", {}).get("count", 0),
                    "posts_count": user_data.get("edge_owner_to_timeline_media", {}).get("count", 0),
                    "bio": user_data.get("biography", ""),
                    "website": user_data.get("external_url", ""),
                    "profile_pic_url": user_data.get("profile_pic_url"),
                    "profile_pic_url_hd": user_data.get("profile_pic_url_hd"),
                    "is_private": user_data.get("is_private", False),
                    "is_verified": user_data.get("is_verified", False),
                    "id": user_data.get("id")
                }
                
                logger.info(f"Successfully retrieved profile for {username}")
                return profile_info
                
            except ValueError:
                logger.error(f"Failed to parse JSON response for {username}")
                return {
                    "success": False,
                    "error": "Failed to parse API response",
                    "status_code": 500
                }
                
        elif response.status_code == 404:
            logger.warning(f"Profile not found: {username}")
            return {
                "success": False,
                "error": "Instagram profile not found",
                "status_code": 404
            }
            
        elif response.status_code == 429:
            logger.error(f"Rate limited by Instagram for {username}")
            return {
                "success": False,
                "error": "Instagram rate limit reached (Too Many Requests). Try again later or add proxies.",
                "status_code": 429
            }
            
        else:
            logger.error(f"Instagram API returned status {response.status_code} for {username}")
            # Try to see if there is error description
            error_msg = f"Instagram returned status code {response.status_code}"
            try:
                err_json = response.json()
                if "message" in err_json:
                    error_msg += f": {err_json['message']}"
            except Exception:
                pass
                
            return {
                "success": False,
                "error": error_msg,
                "status_code": response.status_code
            }
            
    except requests.exceptions.Timeout:
        logger.error(f"Request timeout fetching profile for {username}")
        return {
            "success": False,
            "error": "Connection to Instagram timed out",
            "status_code": 504
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error fetching profile for {username}: {str(e)}")
        return {
            "success": False,
            "error": f"Network error: {str(e)}",
            "status_code": 502
        }
