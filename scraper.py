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
    Supports comma-separated proxy rotation and auto-failover on rate limits.
    
    :param username: The Instagram username to fetch
    :param proxy: Optional comma-separated proxy URLs
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
    
    # Parse proxy list
    proxy_list = []
    if proxy:
        # Split by comma to support multiple rotating proxies
        proxy_list = [p.strip() for p in proxy.split(",") if p.strip()]
        
    # Set number of attempts based on proxy count
    attempts = len(proxy_list) if proxy_list else 1
    max_attempts = min(max(attempts, 1), 5)  # Limit max retries to 5 to avoid excessive load
    
    # Shuffle proxy list to randomize order of use
    available_proxies = list(proxy_list)
    random.shuffle(available_proxies)
    
    last_error_status = 400
    last_error_msg = "Unknown error"
    
    for attempt in range(max_attempts):
        current_proxy = None
        if available_proxies:
            current_proxy = available_proxies.pop(0)
            
        # Configure proxies for request
        req_proxies = None
        if current_proxy:
            req_proxies = {
                "http": current_proxy,
                "https": current_proxy
            }
            logger.info(f"Attempt {attempt + 1}/{max_attempts}: Querying using proxy: {current_proxy}")
        else:
            logger.info(f"Attempt {attempt + 1}/{max_attempts}: Querying directly (no proxy)")
            
        # Select a random user agent
        user_agent = random.choice(USER_AGENTS)
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
        
        try:
            response = requests.get(url, headers=headers, proxies=req_proxies, timeout=12)
            
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
                    
                    logger.info(f"Successfully retrieved profile for {username} on attempt {attempt + 1}")
                    return profile_info
                    
                except ValueError:
                    logger.error(f"Failed to parse JSON response for {username}")
                    last_error_status = 500
                    last_error_msg = "Failed to parse API response"
                    
            elif response.status_code == 404:
                logger.warning(f"Profile not found: {username}")
                return {
                    "success": False,
                    "error": "Instagram profile not found",
                    "status_code": 404
                }
                
            elif response.status_code == 429:
                logger.warning(f"Attempt {attempt + 1} rate limited (429) by Instagram for {username}")
                last_error_status = 429
                last_error_msg = "Instagram rate limit reached (Too Many Requests)."
                
            else:
                logger.warning(f"Attempt {attempt + 1} returned status {response.status_code} for {username}")
                last_error_status = response.status_code
                error_msg = f"Instagram returned status code {response.status_code}"
                try:
                    err_json = response.json()
                    if "message" in err_json:
                        error_msg += f": {err_json['message']}"
                except Exception:
                    pass
                last_error_msg = error_msg
                
        except requests.exceptions.Timeout:
            logger.warning(f"Attempt {attempt + 1} request timeout for {username}")
            last_error_status = 504
            last_error_msg = "Connection to Instagram timed out"
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {attempt + 1} request exception for {username}: {str(e)}")
            last_error_status = 502
            last_error_msg = f"Network error: {str(e)}"
            
    # If we run out of proxies/attempts and all failed
    logger.error(f"Failed to fetch profile for {username} after {max_attempts} attempts.")
    return {
        "success": False,
        "error": f"{last_error_msg} (Tried {max_attempts} connection paths)",
        "status_code": last_error_status
    }
