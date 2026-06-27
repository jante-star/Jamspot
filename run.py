import os
from dotenv import load_dotenv

load_dotenv()

env = os.getenv('FLASK_ENV', 'development')

if env == 'production':
    from app.config import ProductionConfig as config
else:
    from app.config import DevelopmentConfig as config

from app import create_app

app = create_app(config)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=config.DEBUG)
