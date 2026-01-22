import streamlit as st
from openai import OpenAI

# ================= 配置区 =================
# 这里为了方便，我们做了一个输入框让你填 Key，这样你不用改代码
# 以后熟悉了可以把 Key 放在环境变量里
st.set_page_config(page_title="针推临床大脑", page_icon="🩺", layout="mobile")

# ================= 侧边栏：设置与模式 =================
with st.sidebar:
    st.header("⚙️ 设置")
    api_key = st.text_input("请输入 DeepSeek/OpenAI Key", type="password")
    st.info("提示：建议申请 DeepSeek API，便宜且中文医学能力强。")
    
    st.divider()
    
    st.header("📚 模式选择")
    mode = st.radio(
        "选择当前场景：",
        ("🏥 门诊：病种速查", "🦴 科研：脊柱生物力学", "🤚 专科：吴氏大背晃腰法")
    )

# ================= 核心逻辑：定义不同模式的“人设” =================
if mode == "🏥 门诊：病种速查":
    system_prompt = """
    你是一名三甲医院针灸推拿科的主治医师。用户输入病症后，请务必严格按照以下 markdown 格式输出，条理清晰：
    1. **🎯 核心病机**：一句话概括。
    2. **🥩 肌肉/筋膜致病点**：列出具体的肌肉名称、激痛点位置。
    3. **🦴 脊柱/骨骼关注节段**：具体到节段（如 C5-C6, L4-L5）。
    4. **🔨 建议查体**：列出2-3个关键骨科特殊检查。
    5. **💊 治疗方案**：包含针刺穴位、推拿手法重点、正骨方向。
    """
    st.header("🏥 门诊速查模式")
    st.caption("输入病名，快速获取肌肉、骨骼、查体及治疗思路。")

elif mode == "🦴 科研：脊柱生物力学":
    system_prompt = """
    你是一名脊柱生物力学专家。请忽略常规治疗，侧重从“弓弦理论”、“脊柱内外源稳定系统”角度分析。
    重点分析：受力失衡点、代偿机制、杠杆作用。
    """
    st.header("🦴 脊柱力学分析模式")

else: # 吴氏大背晃腰法
    system_prompt = """
    你是“吴氏大背晃腰法”的资深传承人。
    用户输入腰椎病症，请分析：
    1. 是否适用该手法？（适应症/禁忌症判断）
    2. 操作时的发力技巧与注意事项。
    3. 如果进行 sEMG (表面肌电) 研究，建议采集哪些肌肉的数据？
    """
    st.header("🤚 吴氏大背晃腰法专项")

# ================= 聊天界面 =================
# 初始化历史记录
if "messages" not in st.session_state:
    st.session_state.messages = []

# 显示历史对话
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 处理用户输入
if prompt := st.chat_input("请输入病种或临床问题..."):
    if not api_key:
        st.toast("⚠️ 请先在侧边栏输入 API Key！", icon="❌")
    else:
        # 显示用户问题
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 调用 API
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com") # 默认用 DeepSeek
        
        with st.chat_message("assistant"):
            stream = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt} # 这里未来可以把历史记录加上
                ],
                stream=True,
            )
            response = st.write_stream(stream)
        
        # 保存回答
        st.session_state.messages.append({"role": "assistant", "content": response})