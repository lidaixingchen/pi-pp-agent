import streamlit as st
import requests
from datetime import datetime

# API 配置（便于扩展）
API_DOMAIN = "https://api.binance.com/api/v3"
DEFAULT_SYMBOL = "BTCUSDT"


def fetch_btc_price(symbol=DEFAULT_SYMBOL):
    """
    从 Binance API 获取比特币当前价格、24小时价格变化和百分比变化。
    参数：
        symbol (str): 交易对符号，例如 "BTCUSDT"（默认）
    返回：
        last_price (float): 当前价格 (USD)
        price_change (float): 24小时价格变化 (USD)
        price_change_percent (float): 24小时价格变化百分比
    异常：
        抛出 requests.RequestException 或 ValueError
    """
    url = f"{API_DOMAIN}/ticker/24hr?symbol={symbol}"
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    data = response.json()
    last_price = float(data['lastPrice'])
    price_change = float(data['priceChange'])
    price_change_percent = float(data['priceChangePercent'])
    return last_price, price_change, price_change_percent


def main():
    # 页面基础配置
    st.set_page_config(
        page_title="比特币价格",
        page_icon="₿",
        layout="centered"
    )
    st.title("🎯 比特币实时价格")

    # 初始化 session_state 存储数据，保证刷新和重试时保留旧数据
    if "price_data" not in st.session_state:
        st.session_state["price_data"] = None
        st.session_state["data_fetched"] = False
        st.session_state["last_update"] = None

    # 刷新按钮
    refresh = st.button("🔄 刷新价格", use_container_width=True)

    # ------ 数据获取逻辑 ------
    if refresh or not st.session_state["data_fetched"]:
        with st.spinner("正在获取数据..."):
            try:
                last_price, price_change, price_change_percent = fetch_btc_price()
                st.session_state["price_data"] = (last_price, price_change, price_change_percent)
                st.session_state["data_fetched"] = True
                st.session_state["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.success("数据已更新")
            except Exception as e:
                # 对用户隐藏技术细节，显示友好信息
                st.error("数据获取失败，请检查网络连接或稍后重试。")
                # 开发调试时可取消下一行注释以查看详细异常
                # st.exception(e)
                if st.session_state["price_data"] is None:
                    st.info("请点击上方按钮重新获取")

    # ------ 数据展示 ------
    if st.session_state["price_data"] is not None:
        last_price, price_change, price_change_percent = st.session_state["price_data"]

        # 格式化显示
        price_str = f"${last_price:,.2f}"
        change_str = f"${price_change:+.2f}"
        change_percent_str = f"{price_change_percent:+.2f}%"

        # 两列布局：左列（价格+涨跌额），右列（涨跌幅百分比，带颜色）
        col_left, col_right = st.columns([2, 1])
        with col_left:
            st.metric(
                label="当前价格 (USD)",
                value=price_str,
                delta=change_str  # 涨跌额会自动着色（红跌绿涨）
            )
        with col_right:
            # 根据正负设置颜色和箭头
            color = "#00cc00" if price_change_percent >= 0 else "#cc0000"
            arrow = "▲" if price_change_percent >= 0 else "▼"
            st.markdown(
                f"**24h 涨跌幅**<br>"
                f"<span style='font-size: 28px; color: {color}; font-weight: bold;'>"
                f"{arrow} {change_percent_str}</span>",
                unsafe_allow_html=True
            )

        # 显示更新时间
        update_time = st.session_state.get("last_update", "—")
        st.caption(f"最后更新: {update_time}")
        st.caption("数据来源: Binance API")
        st.caption("提示: 点击上方按钮手动刷新数据")
    else:
        # 从未成功获取过数据时，引导用户操作
        st.info("点击上方「刷新价格」按钮获取最新数据")


if __name__ == "__main__":
    main()
