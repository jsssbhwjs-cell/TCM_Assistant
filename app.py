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
    
    # --- 优先从 Secrets 读取 Key ---
    if "SILICON_API_KEY" in st.secrets and "硅基流动" in provider:
        auto_key = st.secrets["SILICON_API_KEY"]
        st.success("✅ 已自动加载云端 Key")
        api_key = auto_key
        # 留个框防止你想临时换号
        user_input_key = st.text_input("API Key (已自动填入)", type="password", placeholder="使用默认 Key...")
        if user_input_key:
            api_key = user_input_key
    else:
        api_key = st.text_input("第二步：输入 API Key", type="password")
    
    st.divider()
    
    st.header("📚 场景模式")
    mode = st.radio(
        "第三步：选择当前场景",
        ("🏥 门诊：深度临床分析", "🦴 科研：脊柱生物力学", "🤚 专科：吴氏大背晃腰法")
    )

# ================= 3. 定义“人设” (System Prompt) - 核心修改区 =================

if "门诊" in mode:
    # --- 这里进行了大幅升级，满足你的 9 点要求 ---
    system_prompt = """
    你是一名三甲医院针灸推拿科的副主任医师，拥有极丰富的临床经验。
    用户输入病种后，请务必严格按照以下 9 点结构输出，**必须使用 Markdown 格式**，重点内容加粗：

    ### 1. 🎯 核心病机
    * (一句话概括该病的生物力学或经络病机)

    ### 2. 🥩 肌肉与筋膜致病点
    * **关键肌肉**：(列出受累肌肉)
    * **类似疼痛点/牵涉痛**：(描述激痛点引起的牵涉痛区域，或容易混淆的疼痛点)

    ### 3. 🦴 脊柱/骨骼关注节段
    * (具体错位或病变节段，如 C5-C6, L4-L5)

    ### 4. 🔨 建议查体 (含简易步骤)
    * **[查体名称]**：(简述操作步骤，如：患者坐位，医生一手按头顶，一手轻叩...)
    * **[查体名称]**：(简述步骤，重点写阳性体征)

    ### 5. 💊 治疗方案
    * **📍 针刺方案**：
        * **[穴位名]**：
            * *肌肉点位*：(例如：穿过斜方肌，深达...)
            * *解剖点位*：(例如：第X颈椎棘突下旁开...)
    * **👐 推拿/正骨**：(简述关键手法思路)

    ### 6. ⚖️ 鉴别诊断
    * (列出 2-3 个易混淆疾病，并说明鉴别要点)

    ### 7. 🔍 易遗漏的诊断细节
    * (临床上容易忽视的病史、体征或影像学表现)

    ### 8. ⚠️ 治疗细节与避坑
    * (针刺深度、方向、危险区域；或手法的力度、禁忌症)

    ### 9. 🌟 临床特效经验 (最有疗效)
    * (该病最有效的“一招鲜”、经验穴、或特定的组合疗法)
    """
    st.header("🏥 门诊：深度临床分析")

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

# 显示历史消息
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 处理用户输入
if prompt := st.chat_input("请输入病种 (如: 肱骨外上髁炎)..."):
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
