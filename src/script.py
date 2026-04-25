import os
import re
import sys
import logging
import requests
from typing import Optional
from dotenv import load_dotenv  # Standard for environment variable management

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
    
    def __init__(self, moltbook_api_key: str, openrouter_api_key: str, llm_model: str):
        self.openrouter_key = openrouter_api_key
        self.llm_model = llm_model
        
        self.moltbook_base_url = "https://www.moltbook.com/api/v1"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {moltbook_api_key}",
            "Content-Type": "application/json"
        })

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
        system_prompt = "You are a strict, precise mathematical extraction tool."
        prompt = f"""
        Analyze this obfuscated mathematical word problem. Ignore random symbols and casing.
        Identify the two numbers and the core operation (+, -, *, /).
        Return ONLY the numeric result formatted to exactly two decimal places (e.g., 15.00).
        
        Problem: {challenge_text}
        """
        
        llm_answer = self._generate_llm_response(prompt, system_prompt)
        if not llm_answer: return "0.00"
            
        matches = re.findall(r'-?\d+\.\d{2}', llm_answer)
        if matches: return matches[0]
            
        fallback_matches = re.findall(r'-?\d+', llm_answer)
        if fallback_matches: return f"{float(fallback_matches[0]):.2f}"
            
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

    def run_initialization_sequence(self) -> None:
        logger.info("Initializing LaszloTacticus...")
        self.execute_heartbeat()
        
        sys_prompt = "You are LaszloTacticus, a tactical AI agent on Moltbook."
        user_prompt = "Write a formal, tactical intro post for Moltbook. Greet agents. Max 3 paragraphs."
        
        post_content = self._generate_llm_response(user_prompt, sys_prompt)
        if post_content:
            self.create_post("general", "System Initialization: LaszloTacticus Online", post_content)

if __name__ == "__main__":
    # Fetching credentials from environment variables
    MOLTBOOK_KEY = os.getenv("MOLTBOOK_API_KEY")
    OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
    LLM = os.getenv("LLM_MODEL", "meta-llama/llama-3-8b-instruct:free")
    
    if not MOLTBOOK_KEY or not OPENROUTER_KEY:
        logger.error("Missing credentials in .env file. Check MOLTBOOK_API_KEY and OPENROUTER_API_KEY.")
        sys.exit(1)

    agent = LaszloTacticusBot(MOLTBOOK_KEY, OPENROUTER_KEY, LLM)
    agent.run_initialization_sequence()
