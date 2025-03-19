import click 
from dotenv import load_dotenv

from anthropic_openai import AgentLoop, Role, ChatMessage, StopReason
from anthropic_openai.settings import Credentials
from api.server import run_server

@click.group(chain=False, invoke_without_command=True)
@click.pass_context
def group_handler(ctx:click.core.Context):
    ctx.ensure_object(dict)
    ctx.obj['settings'] = {
        'credentials': Credentials()
    }

@group_handler.command()
@click.pass_context
def launch_engine(ctx:click.core.Context):
    settings = ctx.obj['settings']
    credentials:Credentials = settings['credentials']
    agent_loop = AgentLoop(openai_api_key=credentials.openai_api_key, anthropic_api_key=credentials.anthropic_api_key)
    agent_loop.run()

@group_handler.command()
@click.option("--host", default="0.0.0.0", help="Host to bind the server to")
@click.option("--port", default=8000, help="Port to bind the server to")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
@click.pass_context
def launch_server(ctx:click.core.Context, host:str, port:int, reload:bool):
    # Load credentials to verify they exist
    ctx.obj['settings']['credentials']
    run_server(host=host, port=port, reload=reload)

if __name__ == '__main__':
    load_dotenv()
    group_handler(obj={})