"""Nakshatra - Vedic Astrology AI Engine (Streamlit frontend, Cycle B1).

Run: streamlit run frontend/streamlit/app.py
Reuses the nakshatra library directly (no HTTP hop); swap to API
calls in Stage B2. Natal chart is computed once and cached in
session state across pages.
"""

from __future__ import annotations

from datetime import date, datetime, time
from typing import cast

import streamlit as st
from dotenv import load_dotenv

from nakshatra.ai.service import RAGService
from nakshatra.core import (
    Ayanamsa,
    BirthData,
    ChartData,
    HouseSystem,
    calculate_chart,
)
from nakshatra.panchanga import calculate_panchanga
from nakshatra.transits import calculate_transits

load_dotenv()

st.set_page_config(page_title="Nakshatra", layout="wide")

COMMON_TIMEZONES = [
    "Asia/Kathmandu", "Asia/Kolkata", "Asia/Dhaka", "Asia/Colombo",
    "Asia/Tokyo", "Asia/Singapore", "Asia/Dubai", "Asia/Jerusalem",
    "Europe/London", "Europe/Paris", "Europe/Berlin", "Europe/Moscow",
    "Africa/Lagos", "Africa/Johannesburg", "America/New_York",
    "America/Chicago", "America/Denver", "America/Los_Angeles",
    "America/Sao_Paulo", "Australia/Sydney", "Pacific/Auckland", "UTC",
]

VARGA_OPTIONS = [
    "D1", "D2", "D3", "D7", "D9", "D10", "D12", "D16", "D20",
    "D24", "D27", "D30", "D40", "D45", "D60",
]


def _birth_form(prefix: str) -> tuple[BirthData, Ayanamsa, HouseSystem] | None:
    """Shared birth-data form. Returns None until submitted."""
    with st.form(prefix):
        col1, col2 = st.columns(2)
        with col1:
            dob = st.date_input(
                "Date of birth", value=date(1990, 1, 1), key=f"{prefix}_dob"
            )
            tob = st.time_input(
                "Time of birth", value=time(12, 0), key=f"{prefix}_tob"
            )
            lat = st.number_input(
                "Latitude", -90.0, 90.0, 27.8667, key=f"{prefix}_lat"
            )
            lon = st.number_input(
                "Longitude", -180.0, 180.0, 83.4833, key=f"{prefix}_lon"
            )
        with col2:
            tz = str(st.selectbox(
                "Timezone", COMMON_TIMEZONES, key=f"{prefix}_tz"
            ))
            place = st.text_input("Place name", "Kathmandu", key=f"{prefix}_place")
            ayanamsa_val = st.selectbox(
                "Ayanamsa",
                list(Ayanamsa),
                index=list(Ayanamsa).index(Ayanamsa.JHORA_LAHIRI),
                key=f"{prefix}_ayanamsa",
            )
            house_system_val = st.selectbox(
                "House system",
                list(HouseSystem),
                index=list(HouseSystem).index(HouseSystem.WHOLE_SIGN),
                key=f"{prefix}_house_system",
            )
        submitted = st.form_submit_button("Calculate")
    if not submitted:
        return None
    data = BirthData(
        year=dob.year,
        month=dob.month,
        day=dob.day,
        hour=tob.hour,
        minute=tob.minute,
        second=tob.second,
        latitude=lat,
        longitude=lon,
        timezone=tz,
        place_name=place or None,
    )
    return data, cast(Ayanamsa, ayanamsa_val), cast(HouseSystem, house_system_val)


def _get_chart(
    birth: BirthData,
    ayanamsa: Ayanamsa = Ayanamsa.JHORA_LAHIRI,
    house_system: HouseSystem = HouseSystem.WHOLE_SIGN,
) -> ChartData:
    """Calculate (and cache) the natal chart in session state."""
    key = (birth, ayanamsa.value, house_system.value)
    if st.session_state.get("chart_key") != key:
        st.session_state.chart = calculate_chart(
            birth=birth, ayanamsa=ayanamsa, house_system=house_system
        )
        st.session_state.chart_key = key
    return cast(ChartData, st.session_state.chart)


def chart_page() -> None:
    """Page 1: birth chart calculation and export."""
    st.title("Birth Chart")
    res = _birth_form("chart")
    if res is None:
        st.info("Enter birth details and press Calculate.")
        return
    birth, ayanamsa, house_system = res
    chart = _get_chart(birth, ayanamsa, house_system)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Planetary positions")
        st.code(chart.to_table())
    with col2:
        st.subheader("South Indian chart")
        varga = st.selectbox("Varga", VARGA_OPTIONS, key="chart_varga")
        st.code(chart.to_diagram(varga=varga))

    st.subheader("Export")
    dl1, dl2, dl3 = st.columns(3)
    dl1.download_button(
        "Download JSON",
        data=chart.model_dump_json(indent=2),
        file_name="chart.json",
        mime="application/json",
    )
    dl2.download_button(
        "Download Markdown",
        data=chart.to_markdown(),
        file_name="chart.md",
        mime="text/markdown",
    )
    dl3.download_button(
        "Download CSV", data=chart.to_csv(), file_name="chart.csv", mime="text/csv"
    )


def transits_page() -> None:
    """Page 2: Gochar transits against the natal chart."""
    st.title("Transits (Gochar)")
    res = _birth_form("transit")
    if res is None:
        st.info("Enter birth details and press Calculate.")
        return
    birth, ayanamsa, house_system = res
    chart = _get_chart(birth, ayanamsa, house_system)

    tdate = st.date_input("Transit date", value=date.today())
    use_natal_location = st.checkbox("Use natal location", value=True)
    tlat = tlon = None
    if not use_natal_location:
        c1, c2 = st.columns(2)
        tlat = c1.number_input("Transit latitude", -90.0, 90.0, 27.8667)
        tlon = c2.number_input("Transit longitude", -180.0, 180.0, 83.4833)

    report = calculate_transits(
        chart,
        transit_date=datetime.combine(tdate, time(12, 0)),
        transit_latitude=tlat,
        transit_longitude=tlon,
    )

    ss = report.sade_sati
    if ss.is_active:
        st.warning(
            f"Sade Sati active: {ss.phase} "
            f"(Saturn in {ss.saturn_sign}, {ss.house_from_moon} from natal Moon)"
        )
    else:
        st.success("No Sade Sati transit active")
    if ss.is_ashtama_shani:
        st.error("Ashtama Shani: Saturn transiting 8th from natal Moon")
    if ss.is_kantaka_shani:
        st.error("Kantaka Shani: Saturn transiting 4th/10th from natal Moon")
    if report.double_transit_houses:
        st.info(
            "Double Transit houses (Jupiter + Saturn aspect): "
            + ", ".join(str(h) for h in report.double_transit_houses)
        )

    st.subheader("Transit report")
    st.code(report.to_table())


def _parse_dt(value: str) -> datetime | None:
    """Parse an ISO timestamp, tolerating a trailing Z."""
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def dasha_page() -> None:
    """Page 3: Vimshottari Dasha timeline with current period."""
    st.title("Vimshottari Dasha Timeline")
    res = _birth_form("dasha")
    if res is None:
        st.info("Enter birth details and press Calculate.")
        return
    birth, ayanamsa, house_system = res
    chart = _get_chart(birth, ayanamsa, house_system)
    dashas = chart.dashas
    if dashas is None:
        st.info("No Dasha data for this chart.")
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Birth nakshatra", dashas.birth_nakshatra)
    c2.metric("Nakshatra lord", dashas.birth_nakshatra_lord)
    c3.metric("Balance lord", dashas.balance_lord)
    c4.metric("Balance (years)", f"{dashas.balance_years:.2f}")

    if dashas.current_md:
        md, ad, pd = dashas.current_md, dashas.current_ad, dashas.current_pd
        st.subheader("Current periods")
        cc1, cc2, cc3 = st.columns(3)
        for col, period, label in (
            (cc1, md, "Mahadasha"),
            (cc2, ad, "Antardasha"),
            (cc3, pd, "Pratyantardasha"),
        ):
            with col:
                if period is None:
                    continue
                start = _parse_dt(period.start)
                end = _parse_dt(period.end)
                if start and end:
                    total = (end - start).total_seconds()
                    elapsed = (
                        datetime.now(start.tzinfo) - start
                    ).total_seconds()
                    fraction = min(max(elapsed / total, 0.0), 1.0)
                else:
                    fraction = 0.0
                st.markdown(f"**{label}: {period.lord}**")
                st.progress(fraction)
                st.caption(f"{period.start} → {period.end}")

    st.subheader("Mahadasha timeline")
    for md in dashas.mahadashas:
        label = f"{md.lord}  ({md.start[:10]} → {md.end[:10]})"
        if md.subs:
            with st.expander(label):
                for ad in md.subs:
                    st.markdown(
                        f"- **{ad.lord}**: {ad.start[:10]} → {ad.end[:10]}"
                    )
        else:
            st.markdown(f"- {label}")


def panchanga_page() -> None:
    """Page 4: daily Panchanga (5 limbs)."""
    st.title("Panchanga")
    with st.form("panchanga"):
        col1, col2 = st.columns(2)
        with col1:
            pdate = st.date_input("Date", value=date.today(), key="panchanga_date")
            ptob = st.time_input(
                "Time", value=time(12, 0), key="panchanga_time"
            )
            plat = st.number_input(
                "Latitude", -90.0, 90.0, 27.8667, key="panchanga_lat"
            )
            plon = st.number_input(
                "Longitude", -180.0, 180.0, 83.4833, key="panchanga_lon"
            )
        with col2:
            ptz = st.selectbox(
                "Timezone", COMMON_TIMEZONES, key="panchanga_tz"
            )
            place = st.text_input(
                "Place name", "Kathmandu", key="panchanga_place"
            )
        submitted = st.form_submit_button("Calculate")
    if not submitted:
        st.info("Enter details and press Calculate.")
        return

    panchanga = calculate_panchanga(
        datetime.combine(pdate, ptob), plat, plon, ptz
    )
    st.subheader(f"Panchanga for {place or pdate}")
    st.code(panchanga.to_table())


def interpret_page() -> None:
    """Page 5: AI interpretation grounded in the classical corpus."""
    st.title("AI Interpretation")
    st.caption(
        "Answers are grounded in the ingested classical corpus with "
        "chapter/verse citations. Configure the index directory and ask "
        "anything (e.g. 'What about my career?')."
    )

    index_dir = st.text_input("Index directory", "index")
    include_chart = st.checkbox(
        "Include my natal chart as context",
        value=False,
        disabled="chart" not in st.session_state,
    )
    question = st.text_area("Your question")

    if not st.button("Ask"):
        return
    if not question.strip():
        st.warning("Please enter a question.")
        return

    try:
        service = RAGService()
        birth_context = None
        if include_chart:
            birth_context = st.session_state.chart.model_dump()
        answer, references = service.ask(
            question,
            index_dir=index_dir,
            birth_context=birth_context,
        )
        st.success(f"Model: {answer.model}  |  References: {len(references)}")
        st.markdown(answer.answer)
        with st.expander(f"Citations ({len(answer.citations)})"):
            for number, citation in enumerate(answer.citations, 1):
                chapter = (
                    f"Chapter {citation.chapter} " if citation.chapter else ""
                )
                verse = (
                    f"Verse {citation.verse}" if citation.verse else ""
                )
                st.markdown(f"**[{number}] {citation.work} {chapter}{verse}**")
                st.caption(citation.text)
    except FileNotFoundError:
        st.error(
            "No index found at that directory. Build one first:\n"
            "`nakshatra ingest-corpus --dir corpus --out index`"
        )
    except Exception as error:  # noqa: BLE001 - surfaced to the user
        st.error(f"Interpretation failed: {error}")


page = st.navigation(
    {
        "Natal": [chart_page, transits_page, dasha_page],
        "Daily": [panchanga_page],
        "AI": [interpret_page],
    }
)
page.run()
