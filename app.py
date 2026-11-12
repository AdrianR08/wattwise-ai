import streamlit as st
from src.dashboard import render_analysis

st.set_page_config(
    page_title="WattWise AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Style the website
st.markdown(
    """
    <style>

    html {
        scroll-behavior: smooth;
    }

    /* Hide the sidebar and its open button */
    [data-testid="stSidebar"],
    [data-testid="stSidebarCollapsedControl"] {
        display: none;
    }

    /* Remove extra space above and below the page */
    .block-container {
        padding-top: 0;
        padding-bottom: 0;
    }

    /* Prevent horizontal scrolling */
    [data-testid="stMain"] {
        overflow-x: hidden;
    }

    /* Style the full-width landing page */
    .landing-page {
        position: relative;
        width: 100vw;
        min-height: 100vh;
        left: 50%;
        transform: translateX(-50%);
        overflow: hidden;
        background-color: #102c4c;

        display: flex;
        justify-content: center;
        align-items: center;
        text-align: center;
        padding: 120px 30px 80px;
    }

    /* Set up the moving background images */
    .landing-image {
        position: absolute;
        inset: 0;
        background-size: cover;
        background-position: center;
        opacity: 0;
        animation: image-cycle 24s infinite;
    }

    .landing-image-one {
        background-image: url(
            "https://images.unsplash.com/photo-1473341304170-971dccb5ac1e?auto=format&fit=crop&w=2000&q=80"
        );
    }

    .landing-image-two {
        background-image: url(
            "https://images.unsplash.com/photo-1509391366360-2e959784a276?auto=format&fit=crop&w=2000&q=80"
        );
        animation-delay: 8s;
    }

    .landing-image-three {
        background-image: url(
            "https://images.unsplash.com/photo-1466611653911-95081537e5b7?auto=format&fit=crop&w=2000&q=80"
        );
        animation-delay: 16s;
    }

    /* Darken the pictures so the text is easier to read */
    .landing-overlay {
        position: absolute;
        inset: 0;
        background: linear-gradient(
            rgba(4, 17, 34, 0.58),
            rgba(4, 17, 34, 0.78)
        );
    }

    .landing-header {
        position: absolute;
        top: 55px;
        left: 8%;
        right: 8%;
        z-index: 1;

        padding-bottom: 22px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.4);

        color: white;
        font-size: 1.2rem;
        font-weight: 700;
        letter-spacing: 3px;
    }

    .landing-content {
        position: relative;
        z-index: 1;
        width: 100%;
        max-width: 850px;
        text-align: center;
    }

    .landing-label {
        color: #8bd5ff;
        font-size: 0.85rem;
        font-weight: 700;
        letter-spacing: 3px;
        text-transform: uppercase;
        margin-bottom: 16px;
    }

    .landing-title {
        color: white !important;
        font-family: Georgia, serif;
        font-size: clamp(2.7rem, 5vw, 5rem) !important;
        font-weight: 400;
        line-height: 1.1;
        margin: 0 0 24px;
    }

    .landing-description {
        color: #edf5ff;
        font-size: clamp(1rem, 1.5vw, 1.2rem);
        line-height: 1.7;
        margin: 0 auto 35px;
        max-width: 750px;
    }

    /* Center the button underneath the description */
    .landing-button {
        display: inline-block;
        background-color: white;
        color: #102b4b !important;
        text-decoration: none !important;
        padding: 15px 36px;
        border-radius: 50px;
        font-size: 0.9rem;
        font-weight: 700;
        letter-spacing: 1px;
        transition: background-color 0.3s ease;
    }

    .landing-button:hover {
        background-color: #a9ddff;
    }

    /* Fade between the pictures while slowly zooming */
    @keyframes image-cycle {
        0% {
            opacity: 0;
            transform: scale(1);
        }
        8% {
            opacity: 1;
        }
        30% {
            opacity: 1;
        }
        38% {
            opacity: 0;
            transform: scale(1.08);
        }
        100% {
            opacity: 0;
            transform: scale(1.08);
        }
    }

    /* Style the dashboard heading */
    .dashboard-header {
        padding: 80px 0 15px;
        scroll-margin-top: 70px;
    }

    .dashboard-label {
        color: #8bd5ff;
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 2px;
        text-transform: uppercase;
    }

    .dashboard-title {
        color: #f1f7ff !important;
        font-size: clamp(2rem, 4vw, 3.2rem) !important;
        margin: 10px 0 6px;
    }

    .dashboard-description {
        color: #a9bfd4;
        font-size: 1rem;
    }

    /* Give the energy metrics a card-like appearance */
    [data-testid="stMetric"] {
        background-color: #142e4b;
        border: 1px solid #284b6a;
        border-radius: 12px;
        padding: 20px;
    }

    /* Style the footer */
    .site-footer {
        position: relative;
        width: 100vw;
        left: 50%;
        transform: translateX(-50%);
        background-color: #031421;
        color: #e6f1ff;
        padding: 70px 8% 35px;
        margin-top: 80px;
    }

    .footer-content {
        display: flex;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 40px;
        max-width: 1300px;
        margin: 0 auto;
    }

    .footer-about {
        max-width: 480px;
    }

    .footer-logo {
        color: white;
        font-size: 1.5rem;
        font-weight: 700;
        letter-spacing: 2px;
        margin-bottom: 20px;
    }

    .footer-description {
        color: #bed0e2;
        line-height: 1.7;
        font-size: 1rem;
    }

    .footer-heading {
        color: white;
        font-size: 1rem;
        font-weight: 700;
        margin-bottom: 12px;
    }

    .footer-bottom {
        max-width: 1300px;
        margin: 50px auto 0;
        padding-top: 25px;
        border-top: 1px solid rgba(255, 255, 255, 0.16);
        color: #a9bfd4;
        font-size: 0.9rem;
    }

    /* Show a still picture for people who prefer less motion */
    @media (prefers-reduced-motion: reduce) {
        html {
            scroll-behavior: auto;
        }

        .landing-image {
            animation: none;
        }

        .landing-image-one {
            opacity: 1;
        }
    }

        /* Center the dashboard headings and descriptions */
    .dashboard-header {
        text-align: center;
    }

    [data-testid="stMain"] h2,
    [data-testid="stMain"] h3 {
        text-align: center;
    }

    [data-testid="stMain"] [data-testid="stMarkdownContainer"] > p,
    [data-testid="stMain"] [data-testid="stCaptionContainer"] {
        text-align: center;
    }

    /* Center the labels above the upload and electricity inputs */
    [data-testid="stWidgetLabel"] {
        display: flex;
        justify-content: center;
        width: 100%;
        text-align: center;
    }

    /* Keep the dashboard a comfortable width and centered */
    .block-container {
        max-width: 1300px;
        margin-left: auto;
        margin-right: auto;
    }

    /* Spread the footer contents across more of the page */
    .footer-content,
    .footer-bottom {
        max-width: none;
        width: 100%;
    }

    /* Keep the footer text left-aligned */
    .site-footer,
    .site-footer p {
        text-align: left !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Display the landing page
st.markdown(
    """
<div class="landing-page">
<div class="landing-image landing-image-one"></div>
<div class="landing-image landing-image-two"></div>
<div class="landing-image landing-image-three"></div>
<div class="landing-overlay"></div>
<div class="landing-header">⚡ WATTWISE AI</div>
<div class="landing-content">
<div class="landing-label">A smarter way to understand energy</div>
<h1 class="landing-title">Take control of your energy</h1>
<p class="landing-description">WattWise AI helps you explore your electricity usage and understand its potential cost. Our project aims to bring energy insights and personalized recommendations together to help you make more informed decisions.</p>
<a class="landing-button" href="#energy-dashboard" target="_self">VIEW DASHBOARD</a>
</div>
</div>
    """,
    unsafe_allow_html=True
)

# Display the dashboard below the landing page
st.markdown(
    """
<div class="dashboard-header" id="energy-dashboard">
<div class="dashboard-label">⚡ WattWise AI / Energy Dashboard</div>
<h1 class="dashboard-title">Make sense of your energy.</h1>
<p class="dashboard-description">Start with a file. Explore the patterns behind your electricity usage.</p>
</div>
    """,
    unsafe_allow_html=True
)

st.divider()

# Allow the user to upload their electricity dataset
st.subheader("Your consumption, all in one place")

st.write(
    "Upload a CSV file containing your electricity consumption data."
)

uploaded_file = st.file_uploader(
    "Upload your electricity consumption CSV file",
    type=["csv"]
)

st.divider()

# Allow the user to enter their electricity settings
st.subheader("Electricity Settings")

electricity_rate = st.number_input(
    "Enter your electricity rate ($/kWh):", min_value=0.0, value=0.15, step=0.01
)

st.divider()

st.subheader("Your Energy Overview")

unit = st.selectbox("Reading units", ["kW", "kWh"], help="Hourly average kW or kWh used during each hour. Cumulative meter readings are not supported.")
timezone = st.text_input("Your data's timezone", value="UTC", help="For example Europe/Oslo or US/Eastern. Used for local calendar months; timestamps may include UTC offsets.")
st.caption("Use hourly readings with timestamp and consumption as the first two columns. Twelve months through the end of a calendar month are needed for a forecast.")

if uploaded_file is not None:
    render_analysis(uploaded_file, unit=unit, timezone=timezone, electricity_rate=electricity_rate)
else:
    st.info("Upload an electricity CSV file to see your consumption, patterns, and next-month forecast.")

st.divider()

# This section can be connected to an AI model later
st.subheader("✦ Ask WattWise")

st.info(
    "In a future version, this section can answer questions "
    "about your electricity usage and provide recommendations."
)

# Display the footer at the end of the page
st.markdown(
    """
<div class="site-footer">
<div class="footer-content">
<div class="footer-about">
<div class="footer-logo">⚡ WATTWISE AI</div>
<p class="footer-description">WattWise AI is a student project designed to help users understand their electricity usage and make more informed energy decisions.</p>
</div>
<div>
<div class="footer-heading">What we explore</div>
<p class="footer-description">Energy analysis<br>Cost estimates<br>Future recommendations</p>
</div>
<div>
<div class="footer-heading">Our goal</div>
<p class="footer-description">Making energy information easier to understand.</p>
</div>
</div>
<div class="footer-bottom">WattWise AI · Student Project</div>
</div>
    """,
    unsafe_allow_html=True
)
