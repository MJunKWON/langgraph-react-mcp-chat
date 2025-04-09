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
from langsmith import Client


memory = MemorySaver()


# API 키 로깅 함수 추가
def check_api_keys():
    """환경 변수에서 API 키들이 제대로 로드되었는지 확인합니다."""
    langsmith_api_key = os.environ.get("LANGSMITH_API_KEY", "없음")
    langsmith_endpoint = os.environ.get("LANGSMITH_ENDPOINT", "없음")
    anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY", "없음")
    openai_api_key = os.environ.get("OPENAI_API_KEY", "없음")
    
    # API 키 마스킹하여 출력 (보안을 위해 첫 8자와 마지막 4자만 표시)
    def mask_key(key):
        if key and len(key) > 12:
            return f"{key[:8]}...{key[-4:]}"
        elif key == "없음":
            return "없음"
        else:
            return "너무 짧은 키"
    
    print("\n===== API 키 확인 =====")
    print(f"LANGSMITH_API_KEY: {mask_key(langsmith_api_key)}")
    print(f"LANGSMITH_ENDPOINT: {langsmith_endpoint}")
    print(f"ANTHROPIC_API_KEY: {mask_key(anthropic_api_key)}")
    print(f"OPENAI_API_KEY: {mask_key(openai_api_key)}")
    print("======================\n")
    
    # LangSmith 활성화 여부 확인
    tracing_enabled = (
        os.environ.get("LANGCHAIN_TRACING_V2", "").lower() == "true" or
        os.environ.get("LANGSMITH_TRACING", "").lower() == "true"
    )
    
    print(f"LangSmith 트레이싱 설정: {'활성화' if tracing_enabled else '비활성화'}")
    print(f"실행 환경: {'Railway/Docker' if os.environ.get('PORT') else '로컬'}")
    
    # LangSmith 키가 없거나 트레이싱이 비활성화된 경우 환경 변수 비활성화
    if langsmith_api_key == "없음" or not tracing_enabled:
        print("LangSmith 트레이싱 비활성화 (API 키 없음 또는 트레이싱 설정 꺼짐)")
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        os.environ["LANGSMITH_TRACING"] = "false"
    else:
        # LangSmith 클라이언트 테스트
        try:
            # 모듈이 있는지 확인
            try:
                from langsmith import Client
            except ImportError:
                print("LangSmith 라이브러리가 설치되지 않았습니다. 트레이싱 비활성화.")
                os.environ["LANGCHAIN_TRACING_V2"] = "false"
                os.environ["LANGSMITH_TRACING"] = "false"
                return

            client = Client()
            projects = list(client.list_projects())
            print(f"LangSmith 연결 성공! 프로젝트 {len(projects)}개 조회됨")
        except Exception as e:
            print(f"LangSmith 연결 실패: {e}")
            print("LangSmith 트레이싱 비활성화 (API 연결 실패)")
            os.environ["LANGCHAIN_TRACING_V2"] = "false"
            os.environ["LANGSMITH_TRACING"] = "false"


@asynccontextmanager
async def make_graph(mcp_tools: Dict[str, Dict[str, str]]):
    async with MultiServerMCPClient(mcp_tools) as client:
        model = ChatAnthropic(
            model="claude-3-7-sonnet", temperature=0.0, max_tokens=800, timeout=60.0
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
    # API 키 확인
    check_api_keys()
    
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
