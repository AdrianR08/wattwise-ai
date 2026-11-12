import streamlit as st
import pandas as pd

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

settings_col1, settings_col2 = st.columns(2)

with settings_col1:
    electricity_rate = st.number_input(
        "Enter your electricity rate ($/kWh):",
        min_value=0.0,
        value=0.15,
        step=0.01
    )

with settings_col2:
    energy_consumed = st.number_input(
        "How many kWh of energy did you consume this month?",
        min_value=0.0,
        value=100.0,
        step=1.0
    )

energy_cost = energy_consumed * electricity_rate

st.caption(
    f"At ${electricity_rate:.2f}/kWh, "
    f"{energy_consumed:,.2f} kWh costs approximately ${energy_cost:,.2f}."
)

st.divider()

st.subheader("Your Energy Overview")

if uploaded_file is not None:

    try:
        df = pd.read_csv(uploaded_file)

        # Check that the dataset contains the columns we need
        required_columns = [
            "timestamp [UTC]",
            "value P [Total active power (kW)]"
        ]

        missing_columns = [
            column for column in required_columns
            if column not in df.columns
        ]

        if missing_columns:
            st.error(
                "The uploaded file is missing these columns: "
                + ", ".join(missing_columns)
            )

        else:
            df["timestamp [UTC]"] = pd.to_datetime(
                df["timestamp [UTC]"],
                errors="coerce"
            )

            df = df.rename(columns={
                "timestamp [UTC]": "Timestamp",
                "value P [Total active power (kW)]": "Power (kW)"
            })

            df["Power (kW)"] = pd.to_numeric(
                df["Power (kW)"],
                errors="coerce"
            )

            # Remove rows without a valid timestamp or power value
            df = df.dropna(subset=["Timestamp", "Power (kW)"])

            if df.empty:
                st.warning(
                    "The file does not contain any usable timestamp "
                    "and power values."
                )

            else:
                average_power = df["Power (kW)"].mean()

                peak_power = df["Power (kW)"].max()

                # This calculation assumes one reading per hour
                seven_day_energy = df.head(168)["Power (kW)"].sum()

                seven_day_cost = seven_day_energy * electricity_rate

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric(
                        label="Energy Used: First 168 Readings",
                        value=f"{seven_day_energy:,.2f} kWh"
                    )

                with col2:
                    st.metric(
                        label="Estimated Cost",
                        value=f"${seven_day_cost:,.2f}"
                    )

                with col3:
                    st.metric(
                        label="Average Power",
                        value=f"{average_power:,.2f} kW"
                    )

                with col4:
                    st.metric(
                        label="Peak Power",
                        value=f"{peak_power:,.2f} kW"
                    )

                st.caption(
                    "Energy and cost estimates assume that each of the "
                    "first 168 readings represents one hour."
                )

                st.divider()

                # Display the graph and an area for future insights
                graph_col, insights_col = st.columns([2, 1])

                with graph_col:
                    st.subheader("Electricity Demand")

                    st.caption("Power use for the first 168 readings")

                    st.line_chart(
                        data=df.head(168),
                        x="Timestamp",
                        y="Power (kW)"
                    )

                with insights_col:
                    st.subheader("Worth a Closer Look")

                    st.write(
                        "Your peak recorded power demand was "
                        f"**{peak_power:,.2f} kW**."
                    )

                    st.write(
                        "Future versions of WattWise can use your data "
                        "to provide more detailed insights and "
                        "recommendations."
                    )

                with st.expander("View your dataset"):
                    st.dataframe(df.head())

    except Exception as error:
        st.error(
            "There was a problem reading this file. "
            "Please check the file and try again."
        )

        st.caption(f"Details: {error}")

else:
    st.info(
        "Upload an electricity CSV file to see your energy overview."
    )

    # Show the dashboard layout before a file is uploaded
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Energy Used", "—")

    with col2:
        st.metric("Estimated Cost", "—")

    with col3:
        st.metric("Average Power", "—")

    with col4:
        st.metric("Peak Power", "—")

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