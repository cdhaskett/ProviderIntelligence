from pathlib import Path
import math

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Provider Coverage Intelligence",
    page_icon="🗺️",
    layout="wide",
)

DATA_DIR = Path(__file__).parent / "data"


@st.cache_data
def load_data():
    providers = pd.read_csv(DATA_DIR / "providers.csv")
    clients = pd.read_csv(DATA_DIR / "client_locations.csv")
    jobs = pd.read_csv(DATA_DIR / "completed_jobs.csv", parse_dates=["completion_date"])
    return providers, clients, jobs


def haversine_miles(lat1, lon1, lat2, lon2):
    radius = 3958.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


providers, clients, jobs = load_data()

st.title("Provider Coverage Intelligence")
st.caption(
    "A portfolio demonstration using fully synthetic provider, client, and job data."
)

finder_tab, gaps_tab, performance_tab = st.tabs(
    ["Provider Finder", "Coverage Gaps", "Performance Overview"]
)

with finder_tab:
    st.subheader("Find qualified providers")

    location_labels = (
        clients["location_id"]
        + " — "
        + clients["site_name"]
        + " ("
        + clients["state"]
        + ")"
    )
    location_lookup = dict(zip(location_labels, clients["location_id"]))

    with st.sidebar:
        st.header("Search Settings")
        selected_location_label = st.selectbox(
            "Client location",
            location_labels.tolist(),
        )
        selected_location_id = location_lookup[selected_location_label]
        selected_client = clients.loc[
            clients["location_id"] == selected_location_id
        ].iloc[0]

        default_service_index = sorted(
            jobs["service"].unique().tolist()
        ).index(selected_client["required_service"])

        selected_service = st.selectbox(
            "Required service",
            sorted(jobs["service"].unique()),
            index=default_service_index,
        )
        radius = st.slider("Search radius (miles)", 25, 250, 100, step=25)
        minimum_rating = st.slider(
            "Minimum provider rating", 2.5, 5.0, 3.5, step=0.1
        )
        allowed_statuses = st.multiselect(
            "Agreement status",
            sorted(providers["agreement_status"].unique()),
            default=["Active", "Expiring Soon"],
        )

    matches = providers[
        providers["services"].str.contains(selected_service, regex=False)
        & (providers["rating"] >= minimum_rating)
        & providers["agreement_status"].isin(allowed_statuses)
    ].copy()

    matches["distance_miles"] = matches.apply(
        lambda row: haversine_miles(
            selected_client["latitude"],
            selected_client["longitude"],
            row["latitude"],
            row["longitude"],
        ),
        axis=1,
    )
    matches = matches[matches["distance_miles"] <= radius].copy()

    matches["availability_score"] = (
        100 - matches["utilization_pct"]
    ).clip(lower=0)
    matches["recommendation_score"] = (
        matches["rating"] * 16
        + matches["availability_score"] * 0.25
        + (radius - matches["distance_miles"]).clip(lower=0) / radius * 20
        - matches["average_response_hours"] * 0.10
    ).round(1)
    matches = matches.sort_values(
        ["recommendation_score", "rating"], ascending=False
    )

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Qualified providers", f"{len(matches):,}")
    kpi2.metric(
        "Average distance",
        f"{matches['distance_miles'].mean():.1f} mi" if not matches.empty else "—",
    )
    kpi3.metric(
        "Average rating",
        f"{matches['rating'].mean():.1f}" if not matches.empty else "—",
    )
    kpi4.metric(
        "Average utilization",
        f"{matches['utilization_pct'].mean():.0f}%" if not matches.empty else "—",
    )

    map_fig = go.Figure()

    map_fig.add_trace(
        go.Scattermapbox(
            lat=[selected_client["latitude"]],
            lon=[selected_client["longitude"]],
            mode="markers",
            marker={"size": 16, "color": "red"},
            text=[selected_client["site_name"]],
            hovertemplate="<b>%{text}</b><br>Client location<extra></extra>",
            name="Client location",
        )
    )

    if not matches.empty:
        map_fig.add_trace(
            go.Scattermapbox(
                lat=matches["latitude"],
                lon=matches["longitude"],
                mode="markers",
                marker={
                    "size": 10,
                    "color": matches["recommendation_score"],
                    "colorscale": "Viridis",
                    "showscale": True,
                    "colorbar": {"title": "Score"},
                },
                text=matches["provider_name"],
                customdata=matches[
                    ["distance_miles", "rating", "utilization_pct", "agreement_status"]
                ],
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "Distance: %{customdata[0]:.1f} miles<br>"
                    "Rating: %{customdata[1]:.1f}<br>"
                    "Utilization: %{customdata[2]:.0f}%<br>"
                    "Agreement: %{customdata[3]}<extra></extra>"
                ),
                name="Qualified providers",
            )
        )

    map_fig.update_layout(
        mapbox={
            "style": "open-street-map",
            "center": {
                "lat": selected_client["latitude"],
                "lon": selected_client["longitude"],
            },
            "zoom": 5.5,
        },
        margin={"l": 0, "r": 0, "t": 20, "b": 0},
        height=500,
        legend={"orientation": "h"},
    )
    st.plotly_chart(map_fig, use_container_width=True)

    st.subheader("Recommended providers")
    display_columns = [
        "provider_id",
        "provider_name",
        "city",
        "state",
        "distance_miles",
        "rating",
        "utilization_pct",
        "average_response_hours",
        "agreement_status",
        "recommendation_score",
    ]
    st.dataframe(
        matches[display_columns].round({"distance_miles": 1}),
        use_container_width=True,
        hide_index=True,
    )

    st.download_button(
        "Download provider recommendations",
        matches[display_columns].to_csv(index=False),
        file_name=f"{selected_location_id}_{selected_service.lower().replace(' ', '_')}_providers.csv",
        mime="text/csv",
        disabled=matches.empty,
    )

with gaps_tab:
    st.subheader("Identify coverage gaps")
    gap_radius = st.slider(
        "Coverage standard (miles)", 25, 200, 75, step=25, key="gap_radius"
    )
    gap_service = st.selectbox(
        "Service to evaluate",
        sorted(jobs["service"].unique()),
        key="gap_service",
    )

    service_providers = providers[
        providers["services"].str.contains(gap_service, regex=False)
        & providers["agreement_status"].isin(["Active", "Expiring Soon"])
    ].copy()

    gap_rows = []
    for _, client in clients.iterrows():
        distances = service_providers.apply(
            lambda row: haversine_miles(
                client["latitude"],
                client["longitude"],
                row["latitude"],
                row["longitude"],
            ),
            axis=1,
        )
        count_in_radius = int((distances <= gap_radius).sum())
        nearest_distance = float(distances.min()) if not distances.empty else None
        gap_rows.append(
            {
                "location_id": client["location_id"],
                "site_name": client["site_name"],
                "city": client["city"],
                "state": client["state"],
                "priority_level": client["priority_level"],
                "providers_in_radius": count_in_radius,
                "nearest_provider_miles": round(nearest_distance, 1)
                if nearest_distance is not None
                else None,
                "coverage_status": (
                    "Critical gap"
                    if count_in_radius == 0
                    else "Thin coverage"
                    if count_in_radius <= 2
                    else "Adequate"
                ),
            }
        )

    gaps = pd.DataFrame(gap_rows).sort_values(
        ["providers_in_radius", "nearest_provider_miles"]
    )

    gap_counts = (
        gaps["coverage_status"]
        .value_counts()
        .rename_axis("coverage_status")
        .reset_index(name="locations")
    )
    gap_chart = px.bar(
        gap_counts,
        x="coverage_status",
        y="locations",
        title=f"{gap_service} coverage at {gap_radius} miles",
        text_auto=True,
    )
    st.plotly_chart(gap_chart, use_container_width=True)

    st.dataframe(gaps, use_container_width=True, hide_index=True)

with performance_tab:
    st.subheader("Historical provider performance")

    completed = jobs[jobs["job_status"] == "Completed"].copy()
    provider_summary = (
        completed.groupby("provider_id", as_index=False)
        .agg(
            completed_jobs=("job_id", "count"),
            total_job_value=("job_cost", "sum"),
            avg_response_hours=("response_hours", "mean"),
            avg_days_to_complete=("days_to_complete", "mean"),
            avg_quality_score=("quality_score", "mean"),
        )
        .merge(
            providers[
                ["provider_id", "provider_name", "state", "rating", "utilization_pct"]
            ],
            on="provider_id",
            how="left",
        )
    )

    p1, p2, p3 = st.columns(3)
    p1.metric("Completed jobs", f"{len(completed):,}")
    p2.metric("Completed job value", f"${completed['job_cost'].sum():,.0f}")
    p3.metric("Average quality score", f"{completed['quality_score'].mean():.2f}")

    top_providers = provider_summary.nlargest(12, "completed_jobs").sort_values(
        "completed_jobs"
    )
    performance_chart = px.bar(
        top_providers,
        x="completed_jobs",
        y="provider_name",
        orientation="h",
        title="Providers with the most completed jobs",
        hover_data=["avg_quality_score", "avg_response_hours"],
    )
    st.plotly_chart(performance_chart, use_container_width=True)

    monthly = (
        completed.assign(month=completed["completion_date"].dt.to_period("M").dt.to_timestamp())
        .groupby("month", as_index=False)["job_cost"]
        .sum()
    )
    monthly_chart = px.line(
        monthly,
        x="month",
        y="job_cost",
        markers=True,
        title="Monthly completed job value",
        labels={"job_cost": "Job value", "month": "Month"},
    )
    st.plotly_chart(monthly_chart, use_container_width=True)

    st.dataframe(
        provider_summary.sort_values("completed_jobs", ascending=False).round(2),
        use_container_width=True,
        hide_index=True,
    )

st.divider()
st.caption(
    "All companies, locations, jobs, and performance metrics in this application are synthetic."
)
