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
from react_agent.api_keys import get_api_key, print_api_key_status, validate_api_keys


memory = MemorySaver()


# API 키 로깅 함수 추가
def check_api_keys():
    """환경 변수에서 API 키들이 제대로 로드되었는지 확인합니다."""
    print_api_key_status()
    
    # API 키 검증 및 환경 변수 설정
    validation = validate_api_keys()
    
    # 환경 변수에 API 키 설정 (외부 모듈에서 가져옴)
    os.environ["OPENAI_API_KEY"] = get_api_key("OPENAI_API_KEY") or ""
    os.environ["ANTHROPIC_API_KEY"] = get_api_key("ANTHROPIC_API_KEY") or ""
    os.environ["LANGSMITH_API_KEY"] = get_api_key("LANGSMITH_API_KEY") or ""
    
    # LangSmith 활성화 여부 확인
    tracing_enabled = (
        os.environ.get("LANGCHAIN_TRACING_V2", "").lower() == "true" or
        os.environ.get("LANGSMITH_TRACING", "").lower() == "true"
    )
    
    print(f"LangSmith 트레이싱 설정: {'활성화' if tracing_enabled else '비활성화'}")
    print(f"실행 환경: {'Railway/Docker' if os.environ.get('PORT') else '로컬'}")
    
    # 실행 환경 변수 목록 출력
    print("\n===== 환경 변수 디버깅 =====")
    print("Railway TOML 변수 사용 여부 확인:")
    for key in sorted(os.environ.keys()):
        if key in ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'LANGSMITH_API_KEY', 'LANGSMITH_ENDPOINT', 'PORT', 'HOST']:
            value = os.environ.get(key)
            if key.endswith('_KEY') and value:
                # API 키 마스킹 처리
                value = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "***"
            print(f"  {key}: {value}")
    print("============================\n")
    
    # LangSmith 키가 없거나 트레이싱이 비활성화된 경우 환경 변수 비활성화
    if not validation["langsmith"] or not tracing_enabled:
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

            # 연결 타임아웃 설정
            import requests
            from requests.adapters import HTTPAdapter, Retry
            
            session = requests.Session()
            retry_strategy = Retry(
                total=3,
                backoff_factor=0.5,
                status_forcelist=[429, 500, 502, 503, 504],
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("http://", adapter)
            session.mount("https://", adapter)
            
            # Client 초기화 시 커스텀 세션 사용
            client = Client(request_timeout=30, session=session)
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
