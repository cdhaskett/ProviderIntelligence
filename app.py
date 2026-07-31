from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import provider_intel as pi

st.set_page_config(
    page_title="Provider Coverage Intelligence",
    page_icon="🗺️",
    layout="wide",
)

DATA_DIR = Path(__file__).parent / "data"


@st.cache_data
def load_data():
    providers = pd.read_csv(DATA_DIR / "providers.csv", dtype={"zip_code": str})
    clients = pd.read_csv(DATA_DIR / "client_locations.csv", dtype={"zip_code": str})
    jobs = pd.read_csv(DATA_DIR / "completed_jobs.csv", parse_dates=["completion_date"])
    provider_services = pd.read_csv(DATA_DIR / "provider_services.csv")
    zip_centroids = pd.read_csv(DATA_DIR / "zip_centroids.csv", dtype={"zip_code": str})
    return providers, clients, jobs, provider_services, zip_centroids


def resolve_origin_from_zip(zip_code, zip_centroids):
    """(lat, lon, label) for a ZIP. Uses the bundled table, then pgeocode."""
    centroid = pi.resolve_zip_centroid(zip_code, zip_centroids.to_dict("records"))
    if centroid is not None:
        return centroid[0], centroid[1], f"ZIP {pi.normalize_zip(zip_code)}"
    try:  # optional: any US ZIP if pgeocode is installed and online
        import pgeocode

        record = pgeocode.Nominatim("us").query_postal_code(pi.normalize_zip(zip_code))
        if record is not None and pd.notna(record.latitude):
            return float(record.latitude), float(record.longitude), f"ZIP {pi.normalize_zip(zip_code)}"
    except Exception:
        pass
    return None


providers, clients, jobs, provider_services, zip_centroids = load_data()
service_options = sorted(provider_services["service"].unique())

st.title("Provider Coverage Intelligence")
st.caption(
    "A portfolio demonstration using fully synthetic provider, client, and job data."
)

finder_tab, gaps_tab, performance_tab = st.tabs(
    ["Provider Finder", "Coverage Gaps", "Performance Overview"]
)

with finder_tab:
    st.subheader("Find qualified providers")

    with st.sidebar:
        st.header("Search Settings")

        origin_mode = st.radio(
            "Search origin", ["Client location", "ZIP code"], horizontal=True
        )

        origin_lat = origin_lon = None
        origin_label = ""
        default_service = service_options[0]

        if origin_mode == "Client location":
            location_labels = (
                clients["location_id"] + " — " + clients["site_name"]
                + " (" + clients["state"] + ")"
            )
            location_lookup = dict(zip(location_labels, clients["location_id"]))
            selected_location_label = st.selectbox(
                "Client location", location_labels.tolist()
            )
            selected_location_id = location_lookup[selected_location_label]
            selected_client = clients.loc[
                clients["location_id"] == selected_location_id
            ].iloc[0]
            origin_lat = float(selected_client["latitude"])
            origin_lon = float(selected_client["longitude"])
            origin_label = f"{selected_client['site_name']} ({selected_client['zip_code']})"
            default_service = selected_client["required_service"]
        else:
            zip_code = st.text_input("Search ZIP code", value="46204", max_chars=10)
            st.caption("Sample markets include 46204, 60601, 45202, 48226, 53202 …")
            resolved = resolve_origin_from_zip(zip_code, zip_centroids)
            if resolved is None:
                st.warning("Couldn't locate that ZIP. Try a sample-market ZIP above.")
            else:
                origin_lat, origin_lon, origin_label = resolved

        service_index = (
            service_options.index(default_service)
            if default_service in service_options else 0
        )
        selected_service = st.selectbox(
            "Required service", service_options, index=service_index
        )
        radius = st.slider("Search radius (miles)", 25, 250, 100, step=25)
        max_drive = st.slider("Max drive time (minutes)", 30, 360, 180, step=15)
        minimum_rating = st.slider("Minimum provider rating", 2.5, 5.0, 3.5, step=0.1)
        allowed_statuses = st.multiselect(
            "Agreement status",
            sorted(providers["agreement_status"].unique()),
            default=["Active", "Expiring Soon"],
        )
        avg_mph = st.slider("Assumed average speed (mph)", 30, 65, 45, step=5)

    if origin_lat is None:
        st.info("Enter a valid search origin in the sidebar to see providers.")
        st.stop()

    # Filter by service via the normalized bridge table
    service_provider_ids = provider_services.loc[
        provider_services["service"] == selected_service, "provider_id"
    ]
    matches = providers[
        providers["provider_id"].isin(service_provider_ids)
        & (providers["rating"] >= minimum_rating)
        & providers["agreement_status"].isin(allowed_statuses)
    ].copy()

    matches["distance_miles"] = matches.apply(
        lambda row: pi.haversine_miles(
            origin_lat, origin_lon, row["latitude"], row["longitude"]
        ),
        axis=1,
    )
    matches["drive_time_min"] = matches["distance_miles"].apply(
        lambda d: pi.estimate_drive_time_minutes(d, avg_mph=avg_mph)
    )
    matches = matches[
        (matches["distance_miles"] <= radius)
        & (matches["drive_time_min"] <= max_drive)
    ].copy()

    matches["recommendation_score"] = matches.apply(
        lambda row: pi.recommendation_score(
            row["rating"], row["utilization_pct"], row["distance_miles"],
            radius, row["average_response_hours"],
        ),
        axis=1,
    )
    matches = matches.sort_values(
        ["recommendation_score", "rating"], ascending=False
    )

    st.caption(f"Searching from **{origin_label}** · {selected_service}")

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Qualified providers", f"{len(matches):,}")
    kpi2.metric(
        "Avg distance",
        f"{matches['distance_miles'].mean():.1f} mi" if not matches.empty else "—",
    )
    kpi3.metric(
        "Avg drive time",
        f"{matches['drive_time_min'].mean():.0f} min" if not matches.empty else "—",
    )
    kpi4.metric(
        "Avg rating",
        f"{matches['rating'].mean():.1f}" if not matches.empty else "—",
    )

    map_fig = go.Figure()
    map_fig.add_trace(
        go.Scattermapbox(
            lat=[origin_lat], lon=[origin_lon], mode="markers",
            marker={"size": 16, "color": "red"},
            text=[origin_label],
            hovertemplate="<b>%{text}</b><br>Search origin<extra></extra>",
            name="Search origin",
        )
    )

    if not matches.empty:
        # Draw a "suggested route" line to the top-ranked provider
        top = matches.iloc[0]
        map_fig.add_trace(
            go.Scattermapbox(
                lat=[origin_lat, top["latitude"]],
                lon=[origin_lon, top["longitude"]],
                mode="lines",
                line={"width": 2, "color": "#e8933a"},
                hoverinfo="skip",
                name=f"Top pick (~{top['drive_time_min']:.0f} min)",
            )
        )
        map_fig.add_trace(
            go.Scattermapbox(
                lat=matches["latitude"], lon=matches["longitude"], mode="markers",
                marker={
                    "size": 10, "color": matches["recommendation_score"],
                    "colorscale": "Viridis", "showscale": True,
                    "colorbar": {"title": "Score"},
                },
                text=matches["provider_name"],
                customdata=matches[
                    ["distance_miles", "drive_time_min", "rating", "agreement_status"]
                ],
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "Distance: %{customdata[0]:.1f} mi<br>"
                    "Drive time: ~%{customdata[1]:.0f} min<br>"
                    "Rating: %{customdata[2]:.1f}<br>"
                    "Agreement: %{customdata[3]}<extra></extra>"
                ),
                name="Qualified providers",
            )
        )

    map_fig.update_layout(
        mapbox={
            "style": "open-street-map",
            "center": {"lat": origin_lat, "lon": origin_lon},
            "zoom": 5.5,
        },
        margin={"l": 0, "r": 0, "t": 20, "b": 0},
        height=500,
        legend={"orientation": "h"},
    )
    st.plotly_chart(map_fig, use_container_width=True)

    st.subheader("Recommended providers")
    display_columns = [
        "provider_id", "provider_name", "city", "state", "zip_code",
        "distance_miles", "drive_time_min", "rating", "utilization_pct",
        "average_response_hours", "agreement_status", "recommendation_score",
    ]
    st.dataframe(
        matches[display_columns].round(
            {"distance_miles": 1, "drive_time_min": 0}
        ),
        use_container_width=True,
        hide_index=True,
    )

    st.download_button(
        "Download provider recommendations",
        matches[display_columns].to_csv(index=False),
        file_name=f"{selected_service.lower().replace(' ', '_').replace('/', '')}_providers.csv",
        mime="text/csv",
        disabled=matches.empty,
    )

with gaps_tab:
    st.subheader("Identify coverage gaps")
    gap_radius = st.slider(
        "Coverage standard (miles)", 25, 200, 75, step=25, key="gap_radius"
    )
    gap_service = st.selectbox("Service to evaluate", service_options, key="gap_service")

    gap_provider_ids = provider_services.loc[
        provider_services["service"] == gap_service, "provider_id"
    ]
    service_providers = providers[
        providers["provider_id"].isin(gap_provider_ids)
        & providers["agreement_status"].isin(["Active", "Expiring Soon"])
    ].copy()

    gap_rows = []
    for _, client in clients.iterrows():
        distances = service_providers.apply(
            lambda row: pi.haversine_miles(
                client["latitude"], client["longitude"],
                row["latitude"], row["longitude"],
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
                if nearest_distance is not None else None,
                "coverage_status": pi.coverage_status(count_in_radius),
            }
        )

    gaps = pd.DataFrame(gap_rows).sort_values(
        ["providers_in_radius", "nearest_provider_miles"]
    )

    gap_counts = (
        gaps["coverage_status"].value_counts()
        .rename_axis("coverage_status").reset_index(name="locations")
    )
    gap_chart = px.bar(
        gap_counts, x="coverage_status", y="locations",
        title=f"{gap_service} coverage at {gap_radius} miles", text_auto=True,
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
            providers[["provider_id", "provider_name", "state", "rating", "utilization_pct"]],
            on="provider_id", how="left",
        )
    )

    p1, p2, p3 = st.columns(3)
    p1.metric("Completed jobs", f"{len(completed):,}")
    p2.metric("Completed job value", f"${completed['job_cost'].sum():,.0f}")
    p3.metric("Average quality score", f"{completed['quality_score'].mean():.2f}")

    top_providers = provider_summary.nlargest(12, "completed_jobs").sort_values("completed_jobs")
    performance_chart = px.bar(
        top_providers, x="completed_jobs", y="provider_name", orientation="h",
        title="Providers with the most completed jobs",
        hover_data=["avg_quality_score", "avg_response_hours"],
    )
    st.plotly_chart(performance_chart, use_container_width=True)

    monthly = (
        completed.assign(month=completed["completion_date"].dt.to_period("M").dt.to_timestamp())
        .groupby("month", as_index=False)["job_cost"].sum()
    )
    monthly_chart = px.line(
        monthly, x="month", y="job_cost", markers=True,
        title="Monthly completed job value",
        labels={"job_cost": "Job value", "month": "Month"},
    )
    st.plotly_chart(monthly_chart, use_container_width=True)

    st.dataframe(
        provider_summary.sort_values("completed_jobs", ascending=False).round(2),
        use_container_width=True, hide_index=True,
    )

st.divider()
st.caption(
    "All companies, locations, jobs, and performance metrics in this application are synthetic. "
    "Drive times are transparent estimates (road distance ÷ average speed), not a live routing service."
)
