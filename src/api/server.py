import uvicorn
from dotenv import load_dotenv

from .app import create_app

app = create_app()

def run_server(host="0.0.0.0", port=8000, reload=False):
    """Run the FastAPI server."""
    uvicorn.run("api.server:app", host=host, port=port, reload=reload)

if __name__ == "__main__":
    load_dotenv()
    run_server(reload=True)