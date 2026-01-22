import streamlit as st
from openai import OpenAI

# ================= 1. 页面基础设置 =================
st.set_page_config(page_title="针推临床大脑", page_icon="🩺", layout="centered")

# ================= 2. 侧边栏：配置区 =================
with st.sidebar:
    st.header("⚙️ 核心设置")
    
    # --- 选择服务商 ---
    provider = st.radio(
        "第一步：选择你的服务商",
        ("硅基流动 (SiliconFlow)", "DeepSeek", "OpenAI")
    )
    
    # --- 自动配置逻辑 ---
    if "硅基流动" in provider:
        st.info("💡 已适配：GLM-4.7")
        base_url = "https://api.siliconflow.cn/v1"
        default_model = "Pro/zai-org/GLM-4.7"
    elif "DeepSeek" in provider:
        st.info("💡 提示：DeepSeek 官方源")
        base_url = "https://api.deepseek.com"
        default_model = "deepseek-chat"
    else:
        st.info("💡 提示：OpenAI 官方源")
        base_url = None
        default_model = "gpt-4o"
        
    model_name = st.text_input("当前模型", value=default_model)
    
    # --- 关键修改：优先从 Secrets 读取 Key ---
    # 检查是否在后台配置了 SILICON_API_KEY
    if "SILICON_API_KEY" in st.secrets and "硅基流动" in provider:
        # 如果后台有 Key，直接读取，不显示在界面上，保护隐私
        auto_key = st.secrets["SILICON_API_KEY"]
        st.success("✅ 已自动加载云端 Key")
        api_key = auto_key # 赋值
        
        # 即使自动加载，也留个框防止你想临时换号（显示为空或占位符）
        user_input_key = st.text_input("第二步：API Key (已自动填入)", type="password", placeholder="使用默认 Key...")
        if user_input_key:
            api_key = user_input_key
    else:
        # 如果没配置 Secrets，就手动输入
        api_key = st.text_input("第二步：输入 API Key", type="password")
    
    st.divider()
    
    st.header("📚 场景模式")
    mode = st.radio(
        "第三步：选择当前场景",
        ("🏥 门诊：病种速查", "🦴 科研：脊柱生物力学", "🤚 专科：吴氏大背晃腰法")
    )

# ================= 3. 定义“人设” (System Prompt) =================
if "门诊" in mode:
    system_prompt = """
    你是一名三甲医院针灸推拿科的主治医师。用户输入病症后，请务必严格按照以下 markdown 格式输出，条理清晰：
    1. **🎯 核心病机**：一句话概括。
    2. **🥩 肌肉/筋膜致病点**：列出具体的肌肉名称、激痛点位置。
    3. **🦴 脊柱/骨骼关注节段**：具体到节段（如 C5-C6, L4-L5）。
    4. **🔨 建议查体**：列出2-3个关键骨科特殊检查。
    5. **💊 治疗方案**：包含针刺穴位、推拿手法重点、正骨方向。
    """
    st.header("🏥 门诊速查模式")
elif "脊柱" in mode:
    system_prompt = """
    你是一名脊柱生物力学专家。请忽略常规治疗，侧重从“弓弦理论”、“脊柱内外源稳定系统”角度分析。
    重点分析：受力失衡点、代偿机制、杠杆作用。
    """
    st.header("🦴 脊柱力学分析模式")
else:
    system_prompt = """
    你是“吴氏大背晃腰法”的资深传承人。
    用户输入腰椎病症，请分析：
    1. 是否适用该手法？（适应症/禁忌症判断）
    2. 操作时的发力技巧与注意事项。
    3. 如果进行 sEMG (表面肌电) 研究，建议采集哪些肌肉的数据？
    """
    st.header("🤚 吴氏大背晃腰法专项")

# ================= 4. 聊天交互逻辑 =================
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("请输入病种 (如: 腰椎小关节紊乱)..."):
    if not api_key:
        st.toast("⚠️ 未检测到 API Key，请检查设置！", icon="❌")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        clean_key = api_key.strip()

        try:
            if base_url:
                client = OpenAI(api_key=clean_key, base_url=base_url)
            else:
                client = OpenAI(api_key=clean_key)

            with st.chat_message("assistant"):
                stream = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    stream=True,
                )
                response = st.write_stream(stream)
            
            st.session_state.messages.append({"role": "assistant", "content": response})

        except Exception as e:
            st.error(f"❌ 通信错误：{e}")
