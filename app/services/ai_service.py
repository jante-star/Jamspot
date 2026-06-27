import requests
import os


class RetellAIService:
    BASE_URL = os.getenv('RETELL_API_BASE_URL', 'https://api.retellai.com')
    API_KEY = os.getenv('RETELL_API_KEY', '')

    @staticmethod
    def _headers():
        return {
            'Authorization': f'Bearer {RetellAIService.API_KEY}',
            'Content-Type': 'application/json',
        }

    @staticmethod
    def create_call_token(user_id, listing_id=None, listing_type=None):
        agent_id = os.getenv('RETELL_AGENT_ID', '')
        if not agent_id:
            print('[RetellAI] RETELL_AGENT_ID not configured')
            return None

        payload = {
            'agent_id': agent_id,
            'metadata': {
                'user_id': user_id or '',
                'listing_id': listing_id or '',
                'listing_type': listing_type or '',
            },
        }
        try:
            r = requests.post(
                f'{RetellAIService.BASE_URL}/v1/create-web-call',
                json=payload,
                headers=RetellAIService._headers(),
                timeout=10,
            )
            return r.json().get('access_token') if r.status_code in (200, 201) else None
        except Exception as e:
            print(f'[RetellAI] create_call_token error: {e}')
            return None
