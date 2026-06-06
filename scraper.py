import requests
import random
import logging
import os

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
    Fetches Instagram profile details.
    1. If RAPIDAPI_KEY is configured in the environment, it uses the RapidAPI scraper.
    2. Otherwise, it falls back to the custom local proxy-rotating scraping engine.
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
        
    # Check if RapidAPI is configured
    rapidapi_key = os.environ.get("RAPIDAPI_KEY")
    if rapidapi_key:
        logger.info(f"RapidAPI key detected. Fetching profile for '{username}' via RapidAPI...")
        result = _fetch_via_rapidapi(username, rapidapi_key)
        if result.get("success"):
            return result
        else:
            logger.warning(f"RapidAPI request failed: {result.get('error')}. Falling back to proxy scraping...")
            
    # Fallback to local scraping with proxies
    return _fetch_via_proxy_scraping(username, proxy)


def _fetch_via_rapidapi(username: str, api_key: str) -> dict:
    """
    Queries the RapidAPI Instagram 120 API endpoint.
    """
    url = "https://instagram120.p.rapidapi.com/api/instagram/profile"
    headers = {
        "Content-Type": "application/json",
        "x-rapidapi-host": "instagram120.p.rapidapi.com",
        "x-rapidapi-key": api_key
    }
    body = {
        "username": username
    }
    
    try:
        response = requests.post(url, headers=headers, json=body, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            user_data = data.get("result")
            
            if not user_data:
                return {
                    "success": False,
                    "error": "RapidAPI returned empty results",
                    "status_code": 404
                }
                
            return {
                "success": True,
                "username": user_data.get("username"),
                "name": user_data.get("full_name") or user_data.get("username"),
                "followers_count": user_data.get("edge_followed_by", {}).get("count", 0),
                "following_count": user_data.get("edge_follow", {}).get("count", 0),
                "posts_count": user_data.get("edge_owner_to_timeline_media", {}).get("count", 0),
                "bio": user_data.get("biography", ""),
                "website": "",  # Not supported in this RapidAPI endpoint
                "profile_pic_url": user_data.get("profile_pic_url"),
                "profile_pic_url_hd": user_data.get("profile_pic_url_hd") or user_data.get("profile_pic_url"),
                "is_private": user_data.get("is_private", False),
                "is_verified": False,  # Not supported in this RapidAPI endpoint
                "id": user_data.get("id"),
                "source": "rapidapi"
            }
        elif response.status_code == 403 or response.status_code == 401:
            return {
                "success": False,
                "error": "Invalid RapidAPI key or subscription inactive",
                "status_code": response.status_code
            }
        elif response.status_code == 429:
            return {
                "success": False,
                "error": "RapidAPI rate limit or quota exceeded",
                "status_code": 429
            }
        else:
            return {
                "success": False,
                "error": f"RapidAPI returned status code {response.status_code}",
                "status_code": response.status_code
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"RapidAPI connection error: {str(e)}",
            "status_code": 502
        }


def _fetch_via_proxy_scraping(username: str, proxy: str = None) -> dict:
    """
    Standard scraper querying Instagram's public API with proxies and failover rotation.
    """
    url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
    
    # Parse proxy list
    proxy_list = []
    if proxy:
        proxy_list = [p.strip() for p in proxy.split(",") if p.strip()]
        
    # Set number of attempts based on proxy count
    attempts = len(proxy_list) if proxy_list else 1
    max_attempts = min(max(attempts, 1), 5)
    
    # Shuffle proxy list
    available_proxies = list(proxy_list)
    random.shuffle(available_proxies)
    
    last_error_status = 400
    last_error_msg = "Unknown error"
    
    for attempt in range(max_attempts):
        current_proxy = None
        if available_proxies:
            current_proxy = available_proxies.pop(0)
            
        req_proxies = None
        if current_proxy:
            req_proxies = {
                "http": current_proxy,
                "https": current_proxy
            }
            logger.info(f"Attempt {attempt + 1}/{max_attempts}: Querying via proxy: {current_proxy}")
        else:
            logger.info(f"Attempt {attempt + 1}/{max_attempts}: Querying directly")
            
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
                        return {
                            "success": False,
                            "error": "Instagram returned empty profile data",
                            "status_code": 404
                        }
                    
                    return {
                        "success": True,
                        "username": user_data.get("username"),
                        "name": user_data.get("full_name") or user_data.get("username"),
                        "followers_count": user_data.get("edge_followed_by", {}).get("count", 0),
                        "following_count": user_data.get("edge_follow", {}).get("count", 0),
                        "posts_count": user_data.get("edge_owner_to_timeline_media", {}).get("count", 0),
                        "bio": user_data.get("biography", ""),
                        "website": user_data.get("external_url", ""),
                        "profile_pic_url": user_data.get("profile_pic_url"),
                        "profile_pic_url_hd": user_data.get("profile_pic_url_hd"),
                        "is_private": user_data.get("is_private", False),
                        "is_verified": user_data.get("is_verified", False),
                        "id": user_data.get("id"),
                        "source": "proxy_scraping"
                    }
                except ValueError:
                    last_error_status = 500
                    last_error_msg = "Failed to parse API response"
            elif response.status_code == 404:
                return {
                    "success": False,
                    "error": "Instagram profile not found",
                    "status_code": 404
                }
            elif response.status_code == 429:
                last_error_status = 429
                last_error_msg = "Instagram rate limit reached (Too Many Requests)."
            else:
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
            last_error_status = 504
            last_error_msg = "Connection to Instagram timed out"
        except requests.exceptions.RequestException as e:
            last_error_status = 502
            last_error_msg = f"Network error: {str(e)}"
            
    logger.error(f"Failed to fetch profile for {username} after {max_attempts} attempts.")
    return {
        "success": False,
        "error": f"{last_error_msg} (Tried {max_attempts} connection paths)",
        "status_code": last_error_status
    }
