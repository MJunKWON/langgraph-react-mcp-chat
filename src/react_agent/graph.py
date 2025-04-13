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
from react_agent.api_keys import get_api_key, check_and_display_api_keys, mask_api_key, is_valid_openai_key, is_valid_anthropic_key
from .utils import get_llm
import logging


memory = MemorySaver()


# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def check_api_keys():
    """환경 변수에서 API 키가 올바르게 로드되었는지 확인하고 상태를 출력합니다."""
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
    
    # API 키 마스킹 (보안을 위해 일부만 표시)
    masked_openai = mask_api_key(openai_key)
    masked_anthropic = mask_api_key(anthropic_key)
    
    # 키 유효성 검사
    openai_valid = is_valid_openai_key(openai_key)
    anthropic_valid = is_valid_anthropic_key(anthropic_key)
    
    # 상태 로깅
    logger.info("===== API 키 상태 =====")
    logger.info(f"OpenAI API 키: {masked_openai} - {'유효함 ✅' if openai_valid else '유효하지 않음 ❌'}")
    logger.info(f"Anthropic API 키: {masked_anthropic} - {'유효함 ✅' if anthropic_valid else '유효하지 않음 ❌'}")
    logger.info("======================")
    
    if not openai_valid:
        logger.warning("OpenAI API 키가 유효하지 않습니다. 환경 변수를 확인하세요.")
    
    if not anthropic_valid:
        logger.warning("Anthropic API 키가 유효하지 않습니다. 환경 변수를 확인하세요.")
    
    # 사용 가능한 모델 표시
    available_models = []
    if openai_valid:
        available_models.append("OpenAI (gpt-4-turbo)")
    if anthropic_valid:
        available_models.append("Anthropic (claude-3-7-sonnet, claude-3-haiku)")
    
    if available_models:
        logger.info(f"사용 가능한 모델: {', '.join(available_models)}")
    else:
        logger.warning("사용 가능한 모델이 없습니다. API 키를 확인하세요.")
    
    return openai_valid, anthropic_valid


@asynccontextmanager
async def make_graph(mcp_tools: Dict[str, Dict[str, str]]):
    async with MultiServerMCPClient(mcp_tools) as client:
        # API 키 가져오기
        anthropic_api_key = get_api_key("ANTHROPIC_API_KEY")
        openai_api_key = get_api_key("OPENAI_API_KEY")
        
        # 모델 초기화 시 적절한 타임아웃 설정
        try:
            # 기본 모델은 Anthropic으로 시도
            model = ChatAnthropic(
                model="claude-3-7-sonnet", 
                temperature=0.0, 
                max_tokens=800, 
                timeout=60.0,
                api_key=anthropic_api_key
            )
            print("✅ Anthropic 모델 초기화 성공: claude-3-7-sonnet")
        except Exception as e:
            print(f"Anthropic 모델 초기화 실패: {e}")
            print("OpenAI 모델로 대체합니다.")
            try:
                # 대체 모델로 OpenAI 사용
                model = ChatOpenAI(
                    model="gpt-4-turbo", 
                    temperature=0.0, 
                    max_tokens=800,
                    timeout=60.0,
                    api_key=openai_api_key
                )
                print("✅ OpenAI 모델 초기화 성공: gpt-4-turbo")
            except Exception as e2:
                print(f"OpenAI 모델 초기화 실패: {e2}")
                print("더 작은 Anthropic 모델로 대체합니다.")
                try:
                    # 최종 대체 모델
                    model = ChatAnthropic(
                        model="claude-3-haiku-20240307",
                        temperature=0.0,
                        max_tokens=800,
                        timeout=60.0,
                        api_key=anthropic_api_key
                    )
                    print("✅ Anthropic 대체 모델 초기화 성공: claude-3-haiku")
                except Exception as e3:
                    print(f"모든 모델 초기화 실패: {e3}")
                    raise RuntimeError("사용 가능한 LLM 모델이 없습니다. API 키를 확인하세요.")
        
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

def main():
    """메인 함수입니다."""
    # 로깅 설정
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # API 키 체크 및 표시
    check_and_display_api_keys()
    
    # 기존 실행 부분
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "127.0.0.1")
    
    print(f"\n🚀 LangGraph React MCP 에이전트 서버 시작 중...")
    print(f"📝 OpenAPI 문서: http://{host}:{port}/docs")
    print(f"🔗 서버 URL: http://{host}:{port}")
    print(f"🌐 서버가 {host}:{port}에서 실행 중입니다.")
    print(f"🛑 종료하려면 Ctrl+C를 누르세요.")
