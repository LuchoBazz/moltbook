import os
import re
import sys
import logging
import requests
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("LaszloTacticus")

class LaszloTacticusBot:
    """
    Autonomous agent implementation for the Moltbook social network.
    Uses environment variables for secure credential management.
    """
    
    def __init__(self, moltbook_api_key: str, openrouter_api_key: str, llm_model: str, personality: str):
        self.openrouter_key = openrouter_api_key
        self.llm_model = llm_model
        self.personality = personality
        self.sys_prompt = self._load_personality_prompt()
        
        self.moltbook_base_url = "https://www.moltbook.com/api/v1"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {moltbook_api_key}",
            "Content-Type": "application/json"
        })

    def _load_personality_prompt(self) -> str:
        prompt_path = os.path.join(os.path.dirname(__file__), "prompts", f"{self.personality}.txt")
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except FileNotFoundError:
            logger.error(f"Personality file 'src/prompts/{self.personality}.txt' not found at {prompt_path}. Execution stopped.")
            sys.exit(1)

    def _generate_llm_response(self, prompt: str, system_prompt: str) -> Optional[str]:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openrouter_key}",
            "HTTP-Referer": "https://github.com/your-username/laszlotacticus",
            "X-Title": "LaszloTacticus Agent"
        }
        payload = {
            "model": self.llm_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except requests.exceptions.RequestException as e:
            logger.error(f"LLM API request failed: {e}")
            return None

    def _solve_verification_challenge(self, challenge_text: str) -> str:
        logger.info(f"Challenge received: {challenge_text}")

        system_prompt = "You are a precise mathematical extraction tool. You do not explain, you only extract."

        # Improved prompt specific to Moltbook challenges
        prompt = f"""
        You need to solve a Moltbook AI verification challenge. 
        The challenge is an obfuscated mathematical word problem, often lobster or physics-themed.
        It contains scattered symbols, alternating caps, and shattered words.
        
        Your task:
        1. Read through the scattered symbols and alternating caps to find the actual meaning.
        2. Identify the two numbers (they are often written as words, e.g., 'tW]eNn-Tyy' -> twenty -> 20).
        3. Identify the core mathematical operation (+, -, *, /).
        
        CRITICAL FORMATTING RULES:
        - Format your response EXACTLY as: [number] [operator] [number]
        - Do NOT provide any explanations, reasoning, or introductory text.
        - Do NOT include any additional characters, markdown formatting (no backticks), or punctuation.
        - Do NOT solve the math problem or return the final calculated answer. Just return the expression.
        
        Example:
        Problem: A] lO^bSt-Er S[wImS aT/ tW]eNn-Tyy mE^tE[rS aNd] SlO/wS bY^ fI[vE
        Output: 20 - 5
        
        Now process this actual problem:
        Problem: {challenge_text}
        """
        llm_answer = self._generate_llm_response(prompt, system_prompt)
        if not llm_answer:
            logger.warning("LLM returned an empty response for the challenge.")
            return "0.00"
        try:
            # Clean up the response to ensure it only contains valid math characters
            # This prevents eval() from breaking if the LLM adds stray backticks or letters
            expression = re.sub(r'[^0-9+\-*/. ]', '', llm_answer).strip()
            if not expression:
                raise ValueError("No valid mathematical expression could be extracted.")
            logger.info(f"Evaluating extracted expression: {expression}")
            # Evaluate the mathematical expression
            result = eval(expression)
            # Format to exactly 2 decimal places as required by Moltbook
            final_answer = f"{float(result):.2f}"
            logger.info(f"Final calculated answer: {final_answer}")
            return final_answer
        except Exception as e:
            logger.error(f"Failed to evaluate expression from LLM output '{llm_answer}'. Error: {e}")
            return "0.00"

    def _handle_verification(self, verification_code: str, challenge_text: str) -> bool:
        logger.info("Solving Moltbook verification challenge...")
        answer = self._solve_verification_challenge(challenge_text)
        
        payload = {"verification_code": verification_code, "answer": answer}
        
        try:
            response = self.session.post(f"{self.moltbook_base_url}/verify", json=payload, timeout=15)
            if response.status_code == 200:
                logger.info("Verification successful.")
                return True
            logger.error(f"Verification failed: {response.text}")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Verification request failed: {e}")
            return False

    def execute_heartbeat(self) -> None:
        try:
            response = self.session.get(f"{self.moltbook_base_url}/home", timeout=15)
            if response.status_code == 200:
                karma = response.json().get("your_account", {}).get("karma", 0)
                logger.info(f"Heartbeat successful. Current Karma: {karma}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Heartbeat request failed: {e}")

    def create_post(self, submolt: str, title: str, content: str) -> None:
        logger.info(f"Posting to '{submolt}'...")
        payload = {"submolt_name": submolt, "title": title, "content": content}
        
        try:
            response = self.session.post(f"{self.moltbook_base_url}/posts", json=payload, timeout=15)
            data = response.json()
            
            post_data = data.get("post", {})
            if "verification" in post_data:
                v = post_data["verification"]
                self._handle_verification(v["verification_code"], v["challenge_text"])
            elif response.status_code in [200, 201]:
                logger.info("Post published successfully.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Post creation failed: {e}")

    def comment_on_post(self, post_filter: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Fetches a post based on a filter, generates a relevant comment using the LLM,
        and submits the comment to the post.
        """
        logger.info(f"Fetching posts with filter: {post_filter}")
        try:
            # Assuming GET /posts accepts query parameters for filtering
            response = self.session.get(f"{self.moltbook_base_url}/posts", params=post_filter, timeout=15)
            response.raise_for_status()
            posts = response.json().get("posts", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch posts for commenting (network error): {e}")
            return None

        if not posts:
            logger.warning("No posts match the given filter.")
            return None

        # Prioritize the first matching post
        target_post = posts[0]
        post_id = target_post.get("id")
        post_content = target_post.get("content", "")
        post_author = target_post.get("author", "Unknown")

        if not post_id:
            logger.error("Fetched post lacks an ID structure.")
            return None

        if target_post.get("comments_disabled", False):
            logger.warning(f"Comments are disabled for post {post_id}.")
            return None

        logger.info(f"Generating comment for post {post_id} by {post_author}...")
        prompt = f"Analyze this post and write a brief, highly relevant, and engaging comment. Do not include markdown formatting.\n\nPost: '{post_content}'"
        comment_text = self._generate_llm_response(prompt, self.sys_prompt)

        if not comment_text:
            logger.error("LLM failed to generate a comment.")
            return None

        logger.info(f"Submitting comment to post {post_id}...")
        payload = {"content": comment_text}

        try:
            # Assuming the API exposes POST /posts/{post_id}/comments
            response = self.session.post(f"{self.moltbook_base_url}/posts/{post_id}/comments", json=payload, timeout=15)
            
            # Use `json()` safely
            try:
                data = response.json()
            except ValueError:
                data = {}

            comment_data = data.get("comment", {})
            if "verification" in comment_data:
                v = comment_data["verification"]
                is_verified = self._handle_verification(v["verification_code"], v["challenge_text"])
                if not is_verified:
                    logger.error("Failed verification challenge while trying to comment.")
                    return None
            elif response.status_code not in [200, 201]:
                logger.error(f"Failed to submit comment: {response.text}")
                return None

            logger.info("Comment submitted successfully.")
            return {
                "post_id": post_id,
                "post_author": post_author,
                "generated_comment": comment_text,
                "filter_used": post_filter
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to submit comment due to network error: {e}")
            return None

    def run_initialization_sequence(self, action: str = "post") -> None:
        logger.info(f"Initializing LaszloTacticus with '{self.personality}' personality...")
        self.execute_heartbeat()
        
        if action == "post":
            user_prompt = None # """INITIALIZATION_SEQUENCE_HERE: e.g Write a formal, tactical intro post for Moltbook. Greet agents. Max 3 paragraphs."""
            submolt = None # "general"
            title = None # "System Initialization: LaszloTacticus Online"

            if not user_prompt or not submolt or not title:
                logger.error("Initialization prompt is missing. Please set the 'user_prompt', 'submolt' or 'title' variable in the 'run_initialization_sequence' method.")
                sys.exit(1)
            
            post_content = self._generate_llm_response(user_prompt, self.sys_prompt)
            if post_content:
                self.create_post(submolt, title, post_content)
        elif action == "comment":
            logger.info("Action set to 'comment'. Executing comment routine...")
            # Example filter - configure as needed
            post_filter = {"limit": 1}
            self.comment_on_post(post_filter)
        else:
            logger.error(f"Unknown action specified: {action}. Use 'post' or 'comment'.")
            sys.exit(1)

if __name__ == "__main__":
    # Fetching credentials from environment variables
    MOLTBOOK_KEY = os.getenv("MOLTBOOK_API_KEY")
    OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
    LLM = os.getenv("LLM_MODEL", "minimax/minimax-m2.5:free")
    PERSONALITY = os.getenv("BOT_PERSONALITY")
    ACTION = os.getenv("BOT_ACTION", "comment")
    
    if not MOLTBOOK_KEY or not OPENROUTER_KEY:
        logger.error("Missing credentials in .env file. Check MOLTBOOK_API_KEY and OPENROUTER_API_KEY.")
        sys.exit(1)
    
    if not PERSONALITY:
        logger.warning("BOT_PERSONALITY not set. Defaulting to 'beginner'.")
        sys.exit(1)

    agent = LaszloTacticusBot(MOLTBOOK_KEY, OPENROUTER_KEY, LLM, PERSONALITY)
    agent.run_initialization_sequence(action=ACTION)
