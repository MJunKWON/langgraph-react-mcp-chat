from datetime import datetime, timezone
from typing import Dict, List, Literal, cast

from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode

from react_agent.configuration import Configuration
from react_agent.state import InputState, State
from react_agent.tools import TOOLS
from react_agent import utils
from contextlib import asynccontextmanager
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import RunnableConfig
import os


memory = MemorySaver()


@asynccontextmanager
async def make_graph(mcp_tools: Dict[str, Dict[str, str]]):
    async with MultiServerMCPClient(mcp_tools) as client:
        # API 키 명시적으로 로드 (디버깅용)
        anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not anthropic_api_key:
            print("경고: ANTHROPIC_API_KEY 환경 변수가 설정되지 않았습니다!")
        else:
            # API 키 로그 출력 (보안상 완전한 키는 출력하지 않음)
            print(f"API 키 형식 확인: {anthropic_api_key[:10]}...{anthropic_api_key[-4:]}")
        
        # LangSmith 환경 변수 확인
        langsmith_api_key = os.environ.get("LANGSMITH_API_KEY")
        langsmith_project = os.environ.get("LANGSMITH_PROJECT")
        langsmith_endpoint = os.environ.get("LANGSMITH_ENDPOINT")
        print(f"LangSmith 설정 확인:")
        print(f"  - API 키: {langsmith_api_key[:10]}...{langsmith_api_key[-4:] if langsmith_api_key else '없음'}")
        print(f"  - 프로젝트: {langsmith_project}")
        print(f"  - 엔드포인트: {langsmith_endpoint}")
            
        model = ChatAnthropic(
            model="claude-3-7-sonnet-latest", 
            temperature=0.0, 
            max_tokens=800, 
            timeout=60.0,
            anthropic_api_key=anthropic_api_key  # API 키 명시적 설정
        )  
        agent = create_react_agent(model, client.get_tools(), checkpointer=memory)
        yield agent


async def call_model(
    state: State, config: RunnableConfig
) -> Dict[str, List[AIMessage]]:
    """Call the LLM powering our "agent".

    This function prepares the prompt, initializes the model, and processes the response.

    Args:
        state (State): The current state of the conversation.
        config (RunnableConfig): Configuration for the model run.

    Returns:
        dict: A dictionary containing the model's response message.
    """
    configuration = Configuration.from_runnable_config(config)

    # Format the system prompt. Customize this to change the agent's behavior.
    system_message = configuration.system_prompt.format(
        system_time=datetime.now(tz=timezone.utc).isoformat()
    )

    mcp_json_path = configuration.mcp_tools

    mcp_tools_config = await utils.load_mcp_config_json(mcp_json_path)

    # Extract the servers configuration from mcpServers key
    mcp_tools = mcp_tools_config.get("mcpServers", {})
    print(mcp_tools)

    response = None

    async with make_graph(mcp_tools) as my_agent:
        # Create the messages list
        messages = [
            SystemMessage(content=system_message),
            *state.messages,
        ]

        # Pass messages with the correct dictionary structure
        response = cast(
            AIMessage,
            await my_agent.ainvoke(
                {"messages": messages},
                config,
            ),
        )

    # Handle the case when it's the last step and the model still wants to use a tool
    if state.is_last_step and response.tool_calls:
        return {
            "messages": [
                AIMessage(
                    id=response.id,
                    content="Sorry, I could not find an answer to your question in the specified number of steps.",
                )
            ]
        }

    # Return the model's response as a list to be added to existing messages
    return {"messages": [response["messages"][-1]]}


# Define a new graph

builder = StateGraph(State, input=InputState, config_schema=Configuration)

# Define the two nodes we will cycle between
builder.add_node(call_model)
builder.add_node("tools", ToolNode(TOOLS))

# Set the entrypoint as `call_model`
# This means that this node is the first one called
builder.add_edge("__start__", "call_model")


def route_model_output(state: State) -> Literal["__end__", "tools"]:
    """Determine the next node based on the model's output.

    This function checks if the model's last message contains tool calls.

    Args:
        state (State): The current state of the conversation.

    Returns:
        str: The name of the next node to call ("__end__" or "tools").
    """
    last_message = state.messages[-1]
    if not isinstance(last_message, AIMessage):
        raise ValueError(
            f"Expected AIMessage in output edges, but got {type(last_message).__name__}"
        )
    # If there is no tool call, then we finish
    if not last_message.tool_calls:
        return "__end__"
    # Otherwise we execute the requested actions
    return "tools"


# Add a conditional edge to determine the next step after `call_model`
builder.add_conditional_edges(
    "call_model",
    # After call_model finishes running, the next node(s) are scheduled
    # based on the output from route_model_output
    route_model_output,
)

# Add a normal edge from `tools` to `call_model`
# This creates a cycle: after using tools, we always return to the model
builder.add_edge("tools", "call_model")

# Compile the builder into an executable graph
# You can customize this by adding interrupt points for state updates
graph = builder.compile(
    interrupt_before=[],  # Add node names here to update state before they're called
    interrupt_after=[],  # Add node names here to update state after they're called
)
graph.name = "ReAct Agent"  # This customizes the name in LangSmith
