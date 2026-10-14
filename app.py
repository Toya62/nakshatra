"""
Hugging Face Spaces Entrypoint for Nakshatra Vedic Astrology Engine.
Serves interactive Gradio Web UI while mounting full FastAPI backend:
- Web UI: https://toya62-nakshatra.hf.space/
- Interactive API Docs: https://toya62-nakshatra.hf.space/docs
- OpenAPI JSON (Perplexity/ChatGPT Actions): https://toya62-nakshatra.hf.space/openapi.json
"""

import os
import sys

# Ensure local nakshatra package is resolvable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn
import gradio as gr

from nakshatra.api import app as api_app
from nakshatra.core import BirthData, calculate_chart, Ayanamsa
from nakshatra.compatibility import calculate_compatibility
from nakshatra.muhurtha import calculate_muhurtha
from nakshatra.transits import calculate_transits

# Hugging Face ZeroGPU compatibility hook
try:
    import spaces

    @spaces.GPU
    def _hf_zerogpu_keepalive():
        return True
except Exception:
    pass


def calculate_chart_ui(year, month, day, hour, minute, lat, lon, tz, ayanamsa):
    try:
        b = BirthData(
            year=int(year),
            month=int(month),
            day=int(day),
            hour=int(hour),
            minute=int(minute),
            second=0,
            latitude=float(lat),
            longitude=float(lon),
            timezone=str(tz).strip(),
        )
        ay = Ayanamsa(ayanamsa) if ayanamsa in [a.value for a in Ayanamsa] else Ayanamsa.JHORA_LAHIRI
        chart = calculate_chart(b, ayanamsa=ay)
        return chart.to_table()
    except Exception as e:
        return f"Error calculating chart: {str(e)}"


def match_compatibility_ui(b_y, b_m, b_d, b_h, b_min, b_lat, b_lon, b_tz,
                           g_y, g_m, g_d, g_h, g_min, g_lat, g_lon, g_tz,
                           b_name, g_name):
    try:
        bride = BirthData(int(b_y), int(b_m), int(b_d), int(b_h), int(b_min), 0, float(b_lat), float(b_lon), str(b_tz).strip(), person_name=b_name)
        groom = BirthData(int(g_y), int(g_m), int(g_d), int(g_h), int(g_min), 0, float(g_lat), float(g_lon), str(g_tz).strip(), person_name=g_name)
        b_c = calculate_chart(bride)
        g_c = calculate_chart(groom)
        res = calculate_compatibility(b_c, g_c)
        return res.to_markdown()
    except Exception as e:
        return f"Error matching compatibility: {str(e)}"


def calculate_muhurtha_ui(year, month, day, hour, minute, lat, lon, tz):
    try:
        res = calculate_muhurtha(
            year=int(year),
            month=int(month),
            day=int(day),
            hour=int(hour),
            minute=int(minute),
            latitude=float(lat),
            longitude=float(lon),
            timezone=str(tz).strip(),
        )
        return res.to_markdown()
    except Exception as e:
        return f"Error calculating muhurtha: {str(e)}"


with gr.Blocks(title="Nakshatra - Vedic Astrology AI Engine") as demo:
    gr.Markdown("# 🪐 Nakshatra — Vedic Astrology AI Engine")
    gr.Markdown(
        "Deterministic Vedic calculations powered by Swiss Ephemeris (`pyswisseph`). "
        "Provides 36-point Ashtakoota compatibility, Muhurtha election scoring, and real-time Gochara transits."
    )

    with gr.Tab("Birth Chart (Kundali)"):
        with gr.Row():
            with gr.Column():
                c_y = gr.Number(value=1997, label="Year")
                c_m = gr.Number(value=5, label="Month")
                c_d = gr.Number(value=22, label="Day")
                c_h = gr.Number(value=4, label="Hour (24h)")
                c_min = gr.Number(value=53, label="Minute")
            with gr.Column():
                c_lat = gr.Number(value=27.8667, label="Latitude (North +)")
                c_lon = gr.Number(value=83.4833, label="Longitude (East +)")
                c_tz = gr.Textbox(value="Asia/Kathmandu", label="Timezone IANA")
                c_ay = gr.Dropdown(
                    choices=[a.value for a in Ayanamsa],
                    value="jhora_lahiri",
                    label="Ayanamsa",
                )
                btn_calc = gr.Button("Calculate Chart", variant="primary")

        out_chart = gr.Code(label="Kundali Calculation Output", language="markdown")
        btn_calc.click(
            calculate_chart_ui,
            inputs=[c_y, c_m, c_d, c_h, c_min, c_lat, c_lon, c_tz, c_ay],
            outputs=[out_chart],
        )

    with gr.Tab("36-Point Ashtakoota Compatibility"):
        with gr.Row():
            with gr.Column():
                gr.Markdown("### Bride Birth Details")
                b_name = gr.Textbox(value="Sita", label="Bride Name")
                b_y = gr.Number(value=1997, label="Year")
                b_m = gr.Number(value=5, label="Month")
                b_d = gr.Number(value=22, label="Day")
                b_h = gr.Number(value=4, label="Hour")
                b_min = gr.Number(value=53, label="Minute")
                b_lat = gr.Number(value=27.8667, label="Latitude")
                b_lon = gr.Number(value=83.4833, label="Longitude")
                b_tz = gr.Textbox(value="Asia/Kathmandu", label="Timezone")
            with gr.Column():
                gr.Markdown("### Groom Birth Details")
                g_name = gr.Textbox(value="Rama", label="Groom Name")
                g_y = gr.Number(value=1995, label="Year")
                g_m = gr.Number(value=11, label="Month")
                g_d = gr.Number(value=28, label="Day")
                g_h = gr.Number(value=8, label="Hour")
                g_min = gr.Number(value=30, label="Minute")
                g_lat = gr.Number(value=28.6139, label="Latitude")
                g_lon = gr.Number(value=77.2090, label="Longitude")
                g_tz = gr.Textbox(value="Asia/Kolkata", label="Timezone")

        btn_match = gr.Button("Run Ashtakoota & Kuja Dosha Match", variant="primary")
        out_match = gr.Markdown(label="Compatibility Result")
        btn_match.click(
            match_compatibility_ui,
            inputs=[
                b_y, b_m, b_d, b_h, b_min, b_lat, b_lon, b_tz,
                g_y, g_m, g_d, g_h, g_min, g_lat, g_lon, g_tz,
                b_name, g_name,
            ],
            outputs=[out_match],
        )

    with gr.Tab("Muhurtha Election Engine"):
        with gr.Row():
            with gr.Column():
                m_y = gr.Number(value=2026, label="Year")
                m_m = gr.Number(value=10, label="Month")
                m_d = gr.Number(value=14, label="Day")
                m_h = gr.Number(value=12, label="Hour")
                m_min = gr.Number(value=0, label="Minute")
            with gr.Column():
                m_lat = gr.Number(value=28.6139, label="Latitude")
                m_lon = gr.Number(value=77.2090, label="Longitude")
                m_tz = gr.Textbox(value="Asia/Kolkata", label="Timezone")
                btn_muh = gr.Button("Calculate Muhurtha", variant="primary")

        out_muh = gr.Markdown(label="Muhurtha Suitability Report")
        btn_muh.click(
            calculate_muhurtha_ui,
            inputs=[m_y, m_m, m_d, m_h, m_min, m_lat, m_lon, m_tz],
            outputs=[out_muh],
        )

    with gr.Tab("API & Perplexity / Claude Integration"):
        gr.Markdown(
            """
            ### Direct Cloud Integrations

            This Hugging Face Space runs both this UI and a production **FastAPI REST API**:
            - **Interactive Swagger Docs**: [`/docs`](/docs)
            - **OpenAPI 3.0 Spec**: [`/openapi.json`](/openapi.json)

            #### Use in Perplexity / ChatGPT Custom GPT:
            1. Copy your Space URL: `https://toya62-nakshatra.hf.space/openapi.json`
            2. In Perplexity Pro / ChatGPT Custom GPT, create a new Action and paste this URL.
            3. Perplexity can now calculate charts, Ashtakoota, and Muhurtha in real time!
            """
        )

# Attach all Nakshatra FastAPI routes onto Gradio's internal FastAPI app
demo.app.include_router(api_app.router)
app = demo.app

if __name__ == "__main__":
    demo.launch(ssr_mode=False, theme=gr.themes.Default())

